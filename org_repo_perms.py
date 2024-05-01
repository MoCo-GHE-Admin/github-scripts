#!/usr/bin/env python
"""
Script to look at repos in an org, and dump the permissions for all singleton permissions (i.e. not owner or team based)
owners have access to EVERYTHING, so not interesting
Teams are covered by org_teams.py which gives membershipm, and org_teams_perms.py which gives the permission of that membership.
But sometimes we just need a dump of everything - so add a flag to look for more than singles
"""

import sys

import alive_progress
import github3
import requests

from github_scripts import utils

# noqa: E231


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Report all permissions given to repos to individuals (not by a team)"
    )
    parser.add_argument("org", type=str, help="The org to work with", action="store")
    parser.add_argument(
        "--repo",
        type=str,
        help="Specify a single repo to work on in the specified org if desired",
        action="store",
    )
    parser.add_argument(
        "--all",
        help="Dump ALL (Well, not owners) permissions, not just non-team singletons",
        action="store_true",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="the graphql URL",
        action="store",
        default="https://api.github.com/graphql",
    )
    args = parser.parse_args()
    return args


def make_query(org, repo, usercursor=None):
    """
    Make the org query for permissions to repos --- handling pagination
    org --- the organization to query
    repo --- the repo to query
    usercursor --- any previous query run to handle for the user side- default to null, assuming first run
    return - the query with org and cursor embedded
    """

    query = f"""
{{
  repository(owner:"{org}", name:"{repo}") {{
    name
    collaborators(first:100, after:USERAFTER) {{
      edges{{
        node{{
          login
        }}
        permission
        permissionSources{{

          sourcePermission:permission
          source {{
            ... on Team {{
                permissionSource: __typename
                teamName: name
            }}
            ... on Organization {{
                permissionSource: __typename
                orgName: name
            }}
            ... on Repository {{
              permissionSource: __typename
              repoName: name
            }}
          }}

        }}
      }}
      pageInfo {{
        hasNextPage
        endCursor
      }}
    }}
  }}
}}
"""  # noqa: E231, E202
    query = query.replace("USERAFTER", f'"{usercursor}"' if usercursor is not None else "null")
    return query


def parse_user_data(userdata, report_all):
    """
    Go through the user data looking for collaborators that get their perms from a singleton entry and report
    Note that we do not report org owners
    param: userdata - the json data from the graphql query
    param: report_all - report team based as well
    result: Dict of '<PERMLEVEL>':[SINGLETONUSERLIST]
    """
    result = {}
    for user in userdata:
        perm = user["permission"]
        for source in user["permissionSources"]:
            if (
                source["source"]["permissionSource"] == "Organization"
                and source["sourcePermission"] == perm
                and perm == "ADMIN"
            ):
                # print("Ignore, as it's from the org that they get admin")
                break
            if report_all or (source["source"]["permissionSource"] == "Repository"):
                if perm in result.keys():
                    result[perm].add(user["node"]["login"])
                else:
                    result[perm] = {user["node"]["login"]}
    return result


def main():
    """
    Query the list of repos for the permissions not given by teams.
    """
    args = parse_arguments()
    if args.repo is None:
        gh_sess = github3.login(token=args.token)
        org = gh_sess.organization(args.org)
        repolist = {x.name for x in org.repositories()}
    else:
        repolist = [args.repo]

    headers = {"content-type": "application/json", "Authorization": "Bearer " + args.token}

    resultdict = {}

    with alive_progress.alive_bar(
        dual_line=True,
        title="Getting Perms",
        file=sys.stderr,
        length=20,
        force_tty=True,
        disable=False,
    ) as bar:
        for repo in repolist:
            # print(f"{repo=}")
            bar.text = f" - checking {repo}..."
            done = False
            cursor = None
            bar()
            while not done:
                resultdict[repo] = {}
                query = make_query(args.org, repo, cursor)
                result = requests.post(url=args.url, json={"query": query}, headers=headers)
                if result.status_code != 200:
                    raise Exception(
                        f"Query failed to run by returning code of"
                        f" {result.status_code}. {query}"
                    )
                resultdict[repo].update(
                    parse_user_data(
                        result.json()["data"]["repository"]["collaborators"]["edges"], args.all
                    )
                )
                if result.json()["data"]["repository"]["collaborators"]["pageInfo"]["hasNextPage"]:
                    print(
                        f"{repo=}, more than 100 contributors, fetching more pages", file=sys.stderr
                    )
                    cursor = result.json()["data"]["repository"]["collaborators"]["pageInfo"][
                        "endCursor"
                    ]
                else:
                    done = True
                utils.check_graphql_rate_remain(args.token, bar=bar)
    outputlist = []
    for repo in resultdict.keys():
        line = f"{repo},"  # noqa: E231
        for perms in resultdict[repo].keys():
            line = line + f"{perms}:{':'.join(resultdict[repo][perms])},"  # noqa: E231
        outputlist.append(line)
    print("RepoName, PermissionsColumns")
    print("\n".join(outputlist))


if __name__ == "__main__":
    main()

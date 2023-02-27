#!/usr/bin/env python
"""
Script to dump all the repos associated with a team, and at what permissions level
Team membership of users is handled by org_teams.py
"""

import sys

import alive_progress
import github3
import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Look through org and report all repos associated with teams and their permission levels, or just one team in the org"
    )
    parser.add_argument("org", type=str, help="The org to work with", action="store")
    parser.add_argument(
        "--team", help="If desired, single team to work with in the org.  Uses team slug only"
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


def make_query(org, team, usercursor=None):
    """
    Make the org query for permissions to repos from a team --- handling pagination
    org --- the organization to query
    team --- the repo to query
    usercursor --- any previous query run to handle for the user side- default to null, assuming first run
    return - the query with org and cursor embedded
    """

    query = f"""
{{
    organization(login:"{org}"){{
    team(slug:"{team}"){{
          name
          repositories(first:100, after:USERAFTER){{
            edges{{
              node{{
                repo_name: name
              }}
              permission
            }}
            pageInfo {{
              hasNextPage
              endCursor
            }}
          }}
    }}
  }}
}}
"""
    query = query.replace("USERAFTER", f'"{usercursor}"' if usercursor is not None else "null")
    return query


def parse_repo_data(repodata):
    """
    Go through the repo data getting repos and their perm levels
    param: repodata - the json from the graphql query
    result: dict of '<PERMLEVEL>':[REPOLIST]
    """
    result = {}
    for repo in repodata:
        perm = repo["permission"]
        if perm in result.keys():
            result[perm].append(repo["node"]["repo_name"])
        else:
            result[perm] = [repo["node"]["repo_name"]]
    return result


def main():
    """
    Query github org and return the mapping of the SAML to GH login
    """
    args = parse_arguments()
    gh_sess = github3.login(token=args.token)
    org = gh_sess.organization(args.org)
    if args.team is None:
        teamlist = {x.slug for x in org.teams()}
    else:
        teamlist = [args.team]

    print(f"{teamlist=}")

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
        for team in teamlist:
            bar.text = f"  - checking {team}"
            done = False
            cursor = None
            bar()
            while not done:
                resultdict[team] = {}
                query = make_query(args.org, team, cursor)
                result = requests.post(url=args.url, json={"query": query}, headers=headers)
                if result.status_code != 200:
                    raise Exception(
                        f"Query failed to run by returning code of"
                        f" {result.status_code}. {query}"
                    )
                resultdict[team].update(
                    parse_repo_data(
                        result.json()["data"]["organization"]["team"]["repositories"]["edges"]
                    )
                )
                if result.json()["data"]["organization"]["team"]["repositories"]["pageInfo"][
                    "hasNextPage"
                ]:
                    print(f"{team=}, more than 100 repos, fetching more pages", file=sys.stderr)
                    cursor = result.json()["data"]["organization"]["team"]["repositories"][
                        "pageInfo"
                    ]["endCursor"]
                else:
                    done = True
                utils.check_graphql_rate_remain(args.token, bar=bar)
    outputlist = []
    for team in resultdict.keys():
        line = f"{team},"
        for perms in resultdict[team].keys():
            line = line + f"{perms}:{':'.join(resultdict[team][perms])},"
        outputlist.append(line)
    print("TeamName, RepoPermissionsColumns")
    print("\n".join(outputlist))


if __name__ == "__main__":
    main()

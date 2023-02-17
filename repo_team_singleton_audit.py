#!/usr/bin/env python
"""
Script to look at repos in an org, and determine if the permissions for a person are coming from the ORG, a TEAM, or the REPO
If they are coming solely from repo, report that, else everything is OK and as well organized as possible.
"""

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Look through repos for permissions given not by a team (a singleton)"
    )
    parser.add_argument("org", type=str, help="The org to work with", action="store")
    parser.add_argument(
        "--repos",
        type=str,
        help="The repos to work on in the specified org",
        action="store",
        nargs="+",
        required=True,
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
"""
    query = query.replace("USERAFTER", f'"{usercursor}"' if usercursor is not None else "null")
    return query


def parse_user_data(userdata):
    """
    Go through the user data looking for collaborators that get their perms from a singleton entry
    param: userdata - the json data from the graphql query
    result: True if there's a singleton, false if not.
    """
    result = False
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
            if source["source"]["permissionSource"] == "Repository":
                # print("OMG, REPO!")
                result = True
    return result


def main():
    """
    Query github org and return the mapping of the SAML to GH login
    """
    args = parse_arguments()

    headers = {"content-type": "application/json", "Authorization": "Bearer " + args.token}

    for repo in args.repos:
        done = False
        cursor = None
        while not done:
            query = make_query(args.org, repo, cursor)
            result = requests.post(url=args.url, json={"query": query}, headers=headers)
            if result.status_code != 200:
                raise Exception(
                    f"Query failed to run by returning code of" f" {result.status_code}. {query}"
                )
            repo_report = False
            repo_report = parse_user_data(
                result.json()["data"]["repository"]["collaborators"]["edges"]
            )
            if repo_report:
                print(f"{repo} has likely singleton access")
                break
            if result.json()["data"]["repository"]["collaborators"]["pageInfo"]["hasNextPage"]:
                print("More than 100 contributors, fetching more pages")
                cursor = result.json()["data"]["repository"]["collaborators"]["pageInfo"][
                    "endCursor"
                ]
            else:
                done = True
                print(f"{repo} appears to be using only teams")


if __name__ == "__main__":
    main()

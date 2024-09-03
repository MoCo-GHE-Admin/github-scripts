#!/usr/bin/env python
"""
Script to get the list of all organizations in the given enterprise.
"""

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(description="Get list of organizations in an enterprise")
    parser.add_argument("enterprise", type=str, help="The enterprise to work on", action="store")
    parser.add_argument(
        "--url",
        type=str,
        help="the graphql URL",
        action="store",
        default="https://api.github.com/graphql",
    )
    args = parser.parse_args()
    return args


def make_query(enterprise, cursor=None):
    """
    Make the org query for SAML ID's --- handling pagination
    enterprise - the enterprise to query
    cursor --- any previous query run to handle - default to null, assuming first run
    return - the query with org and cursor embedded
    """
    query = f"""
{{
  enterprise(slug:\"{enterprise}\"){{
    organizations(first:100, after: AFTER){{
      pageInfo{{
        endCursor
        hasNextPage
      }}
      nodes {{
        login
      }}
    }}
  }}
}}""".replace(
        "AFTER", f'"{cursor}"' if cursor else "null"
    )
    return query


def run_query(enterprise, headers, url):
    """
    Run a query through github's graphql API
    And handling pagination... Note, the query has to have
    a stanza like this to work:
        pageInfo {{
            hasNextPage
            endCursor
        }}

    enterprise -- the enterprise to query
    headers -- string - any headers needed for auth.
    url -- graphql engpoint
    return - either the JSON return, or an exception.
           - note that we strip off the everything except the list of users
           - and it's returned as a dict keyed by the cursor returned by the query
    """

    cursor = None
    has_next_page = True
    data = []

    while has_next_page:
        query = make_query(enterprise, cursor)
        request = requests.post(url=url, json={"query": query}, headers=headers)
        jsonified = request.json()
        # print(f'Result of this loop - {request.json()}')
        if request.status_code != 200:
            raise Exception(
                f"Query failed to run by returning code of" f" {request.status_code}. {query}"
            )
        if "errors" in jsonified.keys():
            raise Exception(f"Error: {jsonified['errors'][0]['message']}")
        try:
            has_next_page = jsonified["data"]["enterprise"]["organizations"]["pageInfo"][
                "hasNextPage"
            ]
        except KeyError:
            # missing scopes or PAT not authorized most likely
            print(jsonified)
            raise Exception("please inspect output above")
        cursor = jsonified["data"]["enterprise"]["organizations"]["pageInfo"]["endCursor"]
        # Get rid of the overarching structures we don't care about in the results
        for node in jsonified["data"]["enterprise"]["organizations"]["nodes"]:
            data.append(node["login"])

    return data


def main():
    """
    Query github org and return the mapping of the SAML to GH login
    """
    args = parse_arguments()

    headers = {"content-type": "application/json", "Authorization": "Bearer " + args.token}

    orglist = run_query(args.enterprise, headers, args.url)
    print("\n".join(orglist))


if __name__ == "__main__":
    main()

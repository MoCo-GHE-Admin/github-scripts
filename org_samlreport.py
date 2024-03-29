#!/usr/bin/env python
"""
Script to get the mapping of SAML source name to GH login name
Used in part for ID, also auditing who's clicked the auth button.

hwine suggests potentially rewriting this to use github3 is possible, and
even if the samlreport isn't included in the library he gives the following example code on how to
make github3.py do things it doesn't know about.
search for OutsideCollaboratorIterator on this page:
https://github.com/mozilla/github-org-scripts/blob/main/notebooks/UserSearchPy3.ipynb
"""

import datetime
import sys

import requests
from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(description="Get SAML account mappings out of a GitHub org")
    parser.add_argument("org", type=str, help="The org to work on", action="store")
    parser.add_argument(
        "--url",
        type=str,
        help="the graphql URL",
        action="store",
        default="https://api.github.com/graphql",
    )
    parser.add_argument(
        "-f", type=str, help="File to store CSV to", action="store", default=None, dest="output"
    )
    args = parser.parse_args()
    return args


def make_query(org, cursor=None):
    """
    Make the org query for SAML ID's --- handling pagination
    org --- the organization to query
    cursor --- any previous query run to handle - default to null, assuming first run
    return - the query with org and cursor embedded
    """
    query = f"""
{{
organization(login: \"{org}\") {{
samlIdentityProvider {{
    ssoUrl,
    externalIdentities(first: 100, after: AFTER) {{
        edges {{
            node {{
                guid,
                samlIdentity {{
                    nameId
                }}
                user {{
                    login
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
}}""".replace(
        "AFTER", f'"{cursor}"' if cursor else "null"
    )
    return query


def run_query(org, headers, url):
    """
    Run a query through github's graphql API
    And handling pagination... Note, the query has to have
    a stanza like this to work:
        pageInfo {{
            hasNextPage
            endCursor
        }}

    org -- the org to query
    headers -- string - any headers needed for auth.
    url -- graphql engpoint
    return - either the JSON return, or an exception.
           - note that we strip off the everything except the list of users
           - and it's returned as a dict keyed by the cursor returned by the query
    """

    cursor = None
    has_next_page = True
    data = {}
    while has_next_page:
        query = make_query(org, cursor)
        request = requests.post(url=url, json={"query": query}, headers=headers)
        jsonified = request.json()
        # print(f'Result of this loop - {request.json()}')
        if request.status_code != 200:
            raise Exception(
                f"Query failed to run by returning code of" f" {request.status_code}. {query}"
            )
        try:
            has_next_page = jsonified["data"]["organization"]["samlIdentityProvider"][
                "externalIdentities"
            ]["pageInfo"]["hasNextPage"]
        except KeyError:
            # missing scopes or PAT not authorized most likely
            print(jsonified)
            raise Exception("please inspect output above")
        cursor = jsonified["data"]["organization"]["samlIdentityProvider"]["externalIdentities"][
            "pageInfo"
        ]["endCursor"]
        # Get rid of the overarching structures we don't care about in the results
        data[cursor] = jsonified["data"]["organization"]["samlIdentityProvider"][
            "externalIdentities"
        ]["edges"]

    return data


def main():
    """
    Query github org and return the mapping of the SAML to GH login
    """
    args = parse_arguments()

    headers = {"content-type": "application/json", "Authorization": "Bearer " + args.token}

    saml_dict = run_query(args.org, headers, args.url)

    # Have the SAML mapping - now let's get the whole list of users for the org
    user_mapping = {}
    gh_sess = login(token=args.token)
    org = gh_sess.organization(args.org)
    memberlist = org.members()
    for user in memberlist:
        user_mapping[user.login] = "None"

    # Now we have the users for the org, with None in the field for SAML name
    # Go through saml, and match up the login to SAML id --- anyone without a
    # SAML will keep "None" in the SAML field.
    for cursor in saml_dict:
        for line in saml_dict[cursor]:
            saml_name = line["node"]["samlIdentity"]["nameId"]
            if line["node"]["user"] is None:
                # Occasionally a user will get an LDAP but no link in github?
                print(f"ERROR: SAML {saml_name} has NO match in github?!", file=sys.stderr)
            else:
                user_mapping[line["node"]["user"]["login"]] = saml_name

    output = sys.stdout
    if args.output is not None:
        output = open(args.output, "w")

    # add header column with structured data
    now_dt = datetime.datetime.now()
    dt_string = now_dt.strftime("%Y%m%dT%H%M%S%z")
    structured_data_header = f"structured-data-header source=org_samlreport_output gh_org={args.org} datetime={dt_string}"
    print(f"SAML,GH Login,{structured_data_header}", file=output)

    for gh_name, ldap in user_mapping.items():
        print(f"{ldap},{gh_name}", file=output)

    if args.output is not None:
        output.close()


if __name__ == "__main__":
    main()

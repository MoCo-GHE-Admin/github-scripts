#!/usr/bin/env python
"""
Script to get the dependency information for a repo.
Source doc : https://til.simonwillison.net/github/dependencies-graphql-api
"""

import alive_progress
import requests
from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(description="Get the dependency for repos in an org")
    parser.add_argument("org", type=str, help="The 'org' to work on", action="store")
    parser.add_argument("package", type=str, help="Package name to look for", action="store")
    parser.add_argument(
        "--url",
        type=str,
        help="the graphql URL",
        action="store",
        default="https://api.github.com/graphql",
    )
    args = parser.parse_args()
    return args


def make_query(org, repo, cursor=None):
    """
    Make the org query for SAML ID's --- handling pagination
    org --- the organization to query
    cursor --- any previous query run to handle - default to null, assuming first run
    return - the query with org and cursor embedded
    """
    query = f"""
{{
repository(owner:\"{org}\", name:\"{repo}\") {{
    dependencyGraphManifests (first:100, after:AFTER) {{
        totalCount
        pageInfo{{
            hasNextPage
            endCursor
        }}
        nodes {{
            filename
        }}
        edges {{
            node {{
                blobPath
                dependencies {{
                    totalCount
                    nodes {{
                        packageName
                        requirements
                        hasDependencies
                        packageManager
                    }}
                }}
            }}
        }}
        pageInfo{{
            hasNextPage
            endCursor
        }}
    }}

}}
}}
""".replace(
        "AFTER", f'"{cursor}"' if cursor else "null"
    )
    return query


def get_cursor(jsonified):
    """
    Return the specific cursor for the pagination of this query, from the jsonified data.
    Cursor location specifics are dependent on the writing of the query - so this function abstracts that
    Param: jsonified - the jsonified data.
    return: the cursor string
    """
    return jsonified["data"]["repository"]["dependencyGraphManifests"]["pageInfo"]["endCursor"]


def next_page(jsonified):
    """
    Return the next page exists boolean for pagination of this query, from the jsonified data.
    page flag location specifics are dependent on the writing of the query - so this function abstracts that
    Param: jsonified - the jsonified data.
    return: the boolean of next page
    """
    return jsonified["data"]["repository"]["dependencyGraphManifests"]["pageInfo"]["hasNextPage"]


def run_query(org, repo, headers, url):
    """
    Run a query through github's graphql API
    And handling pagination... Note, the query has to have
    a stanza like this to work:
        pageInfo {{
            hasNextPage
            endCursor
        }}

    org -- the org to query
    repo -- the repo to look at
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
        query = make_query(org, repo, cursor)
        request = requests.post(url=url, json={"query": query}, headers=headers)
        jsonified = request.json()
        if request.status_code != 200:
            raise Exception(
                f"Query failed to run by returning code of" f" {request.status_code}. {query}"
            )
        try:
            has_next_page = next_page(jsonified)
            cursor = get_cursor(jsonified)
            data[cursor] = jsonified["data"]["repository"]["dependencyGraphManifests"]
        except KeyError:
            print("missing scopes, or PAT not authorized most likely")
            print(f"Data: {jsonified}")
            raise Exception("please inspect output above")
    return data


def main():
    """
    Query github org and return the mapping of the SAML to GH login
    """
    args = parse_arguments()

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + args.token,
        "Accept": "application/vnd.github.hawkgirl-preview+json",
    }

    # Open a gh_sess, get the repos for the org.
    gh_sess = login(token=args.token)
    org_obj = gh_sess.organization(args.org)

    package_list = []
    repolist = org_obj.repositories(type="all")
    with alive_progress.alive_bar(
        manual=True,
        title="fetching list of repos",
        force_tty=True,  # force_tty because we are outputting to stderr now
    ) as bar:
        # materialize the iterator so we can get a count
        repolist = list(repolist)
        bar(1)

    with alive_progress.alive_bar(
        dual_line=True,
        title="getting dependencies",
        force_tty=True,
        disable=False,
    ) as bar:
        for repo in repolist:
            bar.text = f"  - checking {repo.name}..."
            utils.check_rate_remain(gh_sess)
            if repo.archived:
                continue  # Do not process archived
            dependency_dict = run_query(org_obj.login, repo.name, headers, args.url)

            for cursor in dependency_dict:
                for reponode in dependency_dict[cursor]["edges"]:
                    for dep in reponode["node"]["dependencies"]["nodes"]:
                        if dep["packageName"] == args.package:
                            package_list.append(
                                {
                                    "org": org_obj.login,
                                    "repo": repo.name,
                                    "name": dep["packageName"],
                                    "ver": dep["requirements"],
                                }
                            )
            bar()

    # output time!
    print()
    print("Org,Repo,Package,Version Requirement")
    for line in package_list:
        print(f"{line['org']},{line['repo']},{line['name']},{line['ver']}")


if __name__ == "__main__":
    main()

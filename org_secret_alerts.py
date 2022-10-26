#!/usr/bin/env python
"""
Script to pull out any existing security alerts
"""

import argparse
from getpass import getpass

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(
        description="examine org for open security alerts from secret scanning, outputting csv data to pursue the alerts"
    )
    parser.add_argument("org", type=str, help="The org that the repos are in")

    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    args = parser.parse_args()
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def get_secret_alerts(org, token, page=1, url="api.github.com"):
    """
    Get the secret alerts for an org
    :param org: organization name
    :param token: token with read access to the org
    :param page: which page to read
    :param url: URL to use for the API endpoint
    :result: the resultant data
    """
    # method from: https://docs.github.com/en/enterprise-cloud@latest/rest/secret-scanning#list-secret-scanning-alerts-for-an-organization
    headers = {"content-type": "application/json", "Authorization": "token " + token}
    query = f"https://{url}/orgs/{org}/secret-scanning/alerts"
    params = {"per_page": "100", "page": page}
    result = requests.get(headers=headers, url=query, params=params)
    return result


def main():
    """
    Setup the lists, and loop through, handling pagination, and then printing the results at the end.
    """
    args = parse_arguments()

    print("Created At,Repo,State,Secret Type,URL")

    done = False
    page = 1
    while not done:
        data = get_secret_alerts(args.org, args.token, page)
        if data.status_code == 200:
            jsondata = data.json()
            # Print the header
            if len(jsondata) == 0:
                done = True
            for item in range(len(jsondata)):
                repo = jsondata[item]["repository"]["full_name"]
                state = jsondata[item]["state"]
                secret_type = jsondata[item]["secret_type_display_name"]
                created_at = jsondata[item]["created_at"]
                url = jsondata[item]["html_url"]
                # url = f'=HYPERLINK("{jsondata[item]["html_url"]}")'
                print(f"{created_at},{repo},{state},{secret_type},{url}")
            # print(f"{keys=}")
            page += 1
        elif data.status_code == 404:
            print("Resource not found - is secret scanning enabled?")
            done = True
        else:
            print(f"No data found, result code: {data.status_code}")
            done = True


if __name__ == "__main__":
    main()

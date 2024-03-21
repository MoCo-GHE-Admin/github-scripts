#!/usr/bin/env python
"""
Script to pull out any existing security alerts
"""

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="examine org for open security alerts from secret scanning, outputting csv data to pursue the alerts"
    )
    parser.add_argument("org", type=str, help="The org that the repos are in")

    args = parser.parse_args()
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


def get_secret_comment(orgrepo, alert, token, url="api.github.com"):
    """
    Get the comment for an alert.  Works only if there's just one page of alert - which is what should be.
    :param orgrepo: org/repo name
    :param alert: the nubmer of the alert
    :param url: host to connect to
    :result: comma delimited data of interest.  (date closed, closer, status of closure, comment)
    """
    headers = {"content-type": "application/json", "Authorization": "token " + token}
    query = f"https://{url}/repos/{orgrepo}/secret-scanning/alerts/{alert}"
    # print(f"{query=}")
    data = requests.get(headers=headers, url=query)
    jsondata = data.json()
    # Have to check to see if things are None before doing things.
    if jsondata["resolved_by"] is None:
        name = "None"
    else:
        name = jsondata["resolved_by"]["login"]
    result_str = f"{jsondata['resolved_at']},{name},{jsondata['resolution']},{jsondata['resolution_comment']}"
    return result_str


def main():
    """
    Setup the lists, and loop through, handling pagination, and then printing the results at the end.
    """
    args = parse_arguments()

    print("Created At,Repo,State,Secret Type,URL,Date Closed,Closer,Status,Comment")

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
                number = jsondata[item]["number"]
                url = jsondata[item]["html_url"]
                # url = f'=HYPERLINK("{jsondata[item]["html_url"]}")'
                commentdata = get_secret_comment(repo, number, args.token)
                print(f"{created_at},{repo},{state},{secret_type},{url},{commentdata}")
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

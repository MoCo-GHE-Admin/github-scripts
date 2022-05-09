#!/usr/bin/env python
"""
Script to get the PAT owner details from a known PAT.
"""

import argparse

import requests


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(
        description="Get details of a PAT, 'GH name, GH ID, Permissions'"
    )
    parser.add_argument("pat", type=str, help="The PAT to analyze", action="store")
    parser.add_argument(
        "--apihost",
        type=str,
        help="hostname to use for query - api.github.com is default",
        default="api.github.com",
    )
    parser.add_argument("--raw", help="Print out the raw results and headers", action="store_true")
    args = parser.parse_args()
    return args


def analyze_pat(pat, hostname):
    """
    :param pat: The pat to analyze
    :param hostname: the hostname to talk with
    :return: Return the entire json.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "content-type": "application/json",
        "Authorization": "token " + pat,
    }
    query = f"https://{hostname}/user"
    result = requests.get(headers=headers, url=query)
    if result.status_code == 200:
        json = result.json()
        return {"json": json, "headers": result.headers}
        # return f"{json['login']},{json['node_id']},\"{result.headers['X-OAuth-Scopes']}\""
    else:
        print("uh oh")


def main():
    """
    Query github org and return the mapping of the PAT
    """
    args = parse_arguments()
    data = analyze_pat(args.pat, args.apihost)
    if args.raw:
        print(f"Header: {data['headers']}")
        print(f"Results: {data['json']}")
    else:
        print(
            f"{data['json']['login']},{data['json']['node_id']},\"{data['headers']['X-OAuth-Scopes']}\""
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script to add user as a collab to many repos
"""

import argparse
from getpass import getpass

import requests

import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(description="invite user to specified orgs at specified level")
    parser.add_argument("username", type=str, help="The GH user name add")
    parser.add_argument("org", type=str, help="The org that the repos are in")
    parser.add_argument(
        "--repos", type=str, help="The 'repo' to invite to", action="store", nargs="+"
    )
    parser.add_argument(
        "--perms",
        help="permissions to add: read, write, admin.",
        default="read",
        choices=["read", "write", "admin"],
    )

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


def add_user_perm(org, repo, user, perm, token, url="api.github.com"):
    """
    Add a user to an org/repo at perm levels
    :param org: the organization name
    :param repo: the repository
    :param user: the username
    :param perm: the perm level - must be a valid github perm string
    :param token: a token with admin access to the repo
    :param url: API URL to use
    :result: the returned response code
    """
    # method from here: https://docs.github.com/en/rest/reference/collaborators#add-a-repository-collaborator
    headers = {"content-type": "application/json", "Authorization": "token " + token}
    query = f"https://{url}/repos/{org}/{repo}/collaborators/{user}"
    params = f"permission:{perm}"
    result = requests.put(headers=headers, url=query, params=params)
    return result.status_code


def main():
    """
    Setup the lists, and loop through, inviting the user as you go
    """
    args = parse_arguments()
    for repo in args.repos:
        response = add_user_perm(
            org=args.org, repo=repo, user=args.username, perm=args.perms, token=args.token
        )
        if response == 201:
            print(f"User {args.user} added to repo {repo}")
        elif response == 204:
            print(f"User {args.user} already has some level of access to {repo}")
        else:
            print(f"Error adding user to repo, response code: {response}")


if __name__ == "__main__":
    main()

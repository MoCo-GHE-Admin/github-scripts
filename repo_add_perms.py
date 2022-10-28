#!/usr/bin/env python
"""
Script to add user or team to a list of repos
If adding a user, if the user is a member, adds the member, else invites as an OC.
"""

import json
from logging import exception

import requests
from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Parse the command line
    """
    parser = utils.GH_ArgParser(
        description="invite member or team to specified repos at specified level. If adding a user, if the user is a member, adds the member, else invites as an OC."
    )
    parser.add_argument(
        "permtype", choices=["team", "member"], help="team or member - specify type of perm"
    )
    parser.add_argument("name", help="Name of the member or team to add")
    parser.add_argument(
        "--perm",
        help="String of the role name, defaults are 'read', 'write', 'triage', 'maintain', 'admin' - but others can be set by the repo admin",
        required=True,
    )
    parser.add_argument("--org", help="Organization/owner that the repos belong to", required=True)
    parser.add_argument("--repos", nargs="+", help="list of repo names", required=True)
    parser.add_argument(
        "--apihost",
        help="API host to connect to - default api.github.com",
        default="api.github.com",
    )
    args = parser.parse_args()
    return args


def add_user_perm(org, repo, user, perm, token, apihost="api.github.com"):
    """
    :param org: String of org/owner
    :param repo: String of repo name
    :param user: String of user name
    :param perm: String of defined permission role
    :param token: the PAT with write access ot the org/repo
    :param apihost: Host to connect to for query.
    :return: Return the result code of the query.
    """
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": "token " + token}
    query = f"https://{apihost}/repos/{org}/{repo}/collaborators/{user}"
    params = {"permission": perm}
    result = requests.put(headers=headers, url=query, data=json.dumps(params))

    return result.status_code


def add_team_perm(org, repo, team, perm, token, apihost="api.github.com"):
    """
    Add a team to the repository at the specific permission level.
    :param org: String of org/owner
    :param repo: String of repo name
    :param team: String of team name
    :param perm: String of defined permission role
    :param token: the PAT with write access ot the org/repo
    :param apihost: Host to connect to for query.
    :return: Return the result code of the query.
    """
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": "token " + token}
    query = f"https://{apihost}/orgs/{org}/teams/{team}/repos/{org}/{repo}"
    params = {"permission": perm}
    result = requests.put(headers=headers, url=query, data=json.dumps(params))

    return result.status_code


def main():
    """
    Setup and then make the repos have permissions
    """
    args = parse_arguments()

    gh_sess = login(token=args.token)

    # Per this: https://docs.github.com/en/rest/collaborators/collaborators#add-a-repository-collaborator
    # a repo collaborator is what I want.
    for repo in args.repos:
        if args.permtype == "team":
            result = add_team_perm(args.org, repo, args.name, args.perm, args.token, args.apihost)
            if result == 204:
                print(f"Repo: {args.org}/{repo} - Added to {args.name} with {args.perm}")
            else:
                print(
                    f"Repo: {args.org}/{repo} returned an error code, check spelling/org/permission types.  Code: {result}"
                )
        elif args.permtype == "member":
            result = add_user_perm(args.org, repo, args.name, args.perm, args.token, args.apihost)
            if result == 201:
                print(f"User {args.name} added to repository {args.org}/{repo}")
            elif result == 204:
                print(f"User {args.name} already a collab on {args.org}/{repo}")
            elif result == 403:
                print(f"Permission denied for {args.org}/{repo}")
            else:
                f"Repo: {args.org}/{repo} returned an error code, check spelling/org/permission types.  Code: {result}"
        else:
            # How did I get here?
            raise exception("Need to specify either team or member to apply perms for.")
        utils.check_rate_remain(gh_sess)

    # if args.permtype == "team":
    #     # Go figure out the team object
    #     for repo in args.repos:
    #         result = add_team_perm(args.org, repo, args.name, args.perm, args.token, args.apihost)
    #         if result == 204:
    #             print(f"Repo: {args.org}/{repo} - Added to {args.name} with {args.perm}")
    #         else:
    #             print(
    #                 f"Repo: {args.org}/{repo} returned an error code, check spelling/org/permission types.  Code: {result}"
    #             )
    #         utils.check_rate_remain(gh_sess)
    # elif args.permtype == "member":
    #     for repo in args.repos:
    #         result = add_user_perm(args.org, repo, args.name, args.perm, args.token, args.apihost)
    #         if result == 201:
    #             print(f"User {args.name} added to repository {args.org}/{repo}")
    #         elif result == 204:
    #             print(f"User {args.name} already a collab on {args.org}/{repo}")
    #         elif result == 403:
    #             print(f"Permission denied for {args.org}/{repo}")
    #         else:
    #             f"Repo: {args.org}/{repo} returned an error code, check spelling/org/permission types.  Code: {result}"
    #         utils.check_rate_remain(gh_sess)
    # else:
    #     # How did I get here?
    #     raise exception("Need to specify either team or member to apply perms for.")


if __name__ == "__main__":
    main()

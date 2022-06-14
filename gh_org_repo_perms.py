#!/usr/bin/env python
"""
Script to look at an org, and output every users permissions to
the repos.  Including outside collab.
Useful for auditing who has access to what, and pointing out low handing
fruit for potential cleanup.
Note - github API reports perms for users as if the team is the user...
So there's no indication here if the perm is to the user or a team they
belong to.
"""

import argparse
import sys
from getpass import getpass

from github3 import exceptions as gh_exceptions
from github3 import login

import utils

# Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 20


def parse_args():
    """
    Parse the command line.  Required commands is the name of the org
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(
        description="Depending on args, dump all repos in an org, repos for a user or users for a repo, and their user permissions, defaults to all repos and users in an org."
    )
    parser.add_argument("org", help="The org to examine", action="store")
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    analyse_group = parser.add_mutually_exclusive_group()
    analyse_group.add_argument("--user", help="Single user to examine in the org")
    analyse_group.add_argument("--repo", help="Single repo to examine in the org")
    parser.add_argument(
        "-i",
        action="store_true",
        default=False,
        dest="info",
        help="Give visual output of that progress continues - "
        "useful for long runs redirected to a file",
    )
    args = parser.parse_args()
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def list_to_str(input_list):
    """
    Given an input list, return a comma delimited string of the list items
    :param input_list: The list to work with
    :result: the comma delimited string
    """
    firstcol = True
    outstr = ""
    for item in input_list:
        if firstcol:
            outstr = str(item)
            firstcol = False
        else:
            outstr += f",{str(item)}"
    return outstr


def main():
    """
    Parse the args, connect to github, get the list of users in the org.
    Then go through the repos and update the users with usage counts.
    {user:{role: orgrole, team:count, repo:count}}
    leaving team in for now - but not updating it
    """
    args = parse_args()
    userlist = {}
    gh_sess = login(token=args.token)

    org = gh_sess.organization(args.org)
    # If a user was specified, just do that one, else, list all org members
    if args.user is None:
        memberlist = org.members(role="member")
    else:
        memberlist = [gh_sess.user(args.user)]
    for member in memberlist:
        userlist[member.login] = {
            "role": "member",
            "privpull": [],
            "privpush": [],
            "privadmin": [],
            "pubpull": [],
            "pubpush": [],
            "pubadmin": [],
        }

    if args.user is None:
        adminlist = org.members(role="admin")
        for admin in adminlist:
            userlist[admin.login] = {
                "role": "admin",
                "privpull": [],
                "privpush": [],
                "privadmin": [],
                "pubpull": [],
                "pubpush": [],
                "pubadmin": [],
            }

    # great, we have initialized our lists - now to go through the repos

    # If a repo is specified, just look at that one, otherwise all of them in the org.
    if args.repo is None:
        repolist = org.repositories()
    else:
        repolist = [gh_sess.repository(args.org, args.repo)]
    # FIXME Should I pull out "-ghsa-" repos - they NEVER find perms right.
    # Alternatively, just silently pass the NotFoundError?  (don't like that at first blush)
    for repo in repolist:
        # print(f'DEBUG: repo: {repo.name}', file=sys.stderr)
        if repo.archived:
            repo_name = f"*{repo.name}"
        else:
            repo_name = repo.name
        try:
            repocollabs = repo.collaborators()
            for collaborator in repocollabs:
                # print(f'collab: {collaborator.login}, repo: {repo.name}, '
                # f'perms: {collaborator.permissions}', file=sys.stderr)
                # go through and update their items
                # External collabs aren't in the list already, so add them
                if args.user is None or args.user == collaborator.login:
                    if collaborator.login not in userlist:
                        userlist[collaborator.login] = {
                            "role": "outside",
                            "privpull": [],
                            "privpush": [],
                            "privadmin": [],
                            "pubpull": [],
                            "pubpush": [],
                            "pubadmin": [],
                        }
                    if repo.private:
                        if collaborator.permissions["admin"]:
                            userlist[collaborator.login]["privadmin"].append(repo_name)
                        if collaborator.permissions["push"]:
                            userlist[collaborator.login]["privpush"].append(repo_name)
                        if collaborator.permissions["pull"]:
                            userlist[collaborator.login]["privpull"].append(repo_name)
                    else:
                        if collaborator.permissions["admin"]:
                            userlist[collaborator.login]["pubadmin"].append(repo_name)
                        if collaborator.permissions["push"]:
                            userlist[collaborator.login]["pubpush"].append(repo_name)
                        if collaborator.permissions["pull"]:
                            userlist[collaborator.login]["pubpull"].append(repo_name)
            utils.check_rate_remain(gh_sess, RATE_PER_LOOP, args.info)
            if args.info:
                utils.spinner()
        except gh_exceptions.NotFoundError as err:
            print(
                f"In repo {repo.name} and collab {collaborator.login} : {err.message}",
                file=sys.stderr,
            )
        except gh_exceptions.ServerError:
            print(f"50X error when processing repo: {repo_name} and collab {collaborator.login}")

    # Print The Things.
    if args.info:
        print(file=sys.stderr)
    print(
        "Username, ORG Role, pub-count, priv-count, pub-pull, pub-push, pub-admin,"
        " priv-pull, priv-push, priv-admin"
    )
    for username, data in userlist.items():
        pubcount = len(data["pubpull"]) + len(data["pubpush"]) + len(data["pubadmin"])
        privcount = len(data["privpull"]) + len(data["privpush"]) + len(data["privadmin"])
        print(
            f'{username},{data["role"]},{pubcount},{privcount},"{list_to_str(data["pubpull"])}",'
            f'"{list_to_str(data["pubpush"])}","{list_to_str(data["pubadmin"])}",'
            f'"{list_to_str(data["privpull"])}","{list_to_str(data["privpush"])}",'
            f'"{list_to_str(data["privadmin"])}"'
        )


if __name__ == "__main__":
    main()

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
import os
import sys
from getpass import getpass

import alive_progress
from github3 import login

import utils


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

    # we disable certain output if the terminal isn't interactive
    session_is_interactive = False
    if os.isatty(sys.stdout.fileno()):
        session_is_interactive = True

    userlist = {}
    # function-based code
    gh_sess = login(token=args.token)
    # object-based code
    ghq = utils.GHPermsQuery()
    ghq.init_gh_session(token=args.token)

    org = gh_sess.organization(args.org)

    # If a user was specified, just do that one, else, list all org members
    if args.user is None:
        memberlist = org.members(role="member")
    else:
        memberlist = [gh_sess.user(args.user)]

    # initialize lists
    empty_entry_dict = {
        "role": "UNSET",
        "privpull": [],
        "privpush": [],
        "privadmin": [],
        "pubpull": [],
        "pubpush": [],
        "pubadmin": [],
    }

    for member in memberlist:
        userlist[member.login] = empty_entry_dict
        userlist[member.login]["role"] = "member"

    if args.user is None:
        adminlist = org.members(role="admin")
        for admin in adminlist:
            userlist[admin.login] = empty_entry_dict
            userlist[admin.login]["role"] = "admin"

    # retrieve list of repos
    # If a repo is specified, just look at that one, otherwise all of them in the org.
    if args.repo is None:
        # TESTING
        # repolist = org.repositories(number=100)
        repolist = org.repositories()
    else:
        repolist = [gh_sess.repository(args.org, args.repo)]

    with alive_progress.alive_bar(
        manual=True,
        title="fetching list of repos",
        force_tty=True,  # force_tty because we are outputting to stderr now
    ) as bar:
        # materialize the iterator so we can get a count
        repolist = list(repolist)
        bar(1)

    # FIXME Should I pull out "-ghsa-" repos - they NEVER find perms right.
    # Alternatively, just silently pass the NotFoundError?  (don't like that at first blush)
    userlist = ghq.update_userlist_with_permission_data(
        userlist, repolist, user=args.user, session_is_interactive=session_is_interactive
    )

    # Print The Things.
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

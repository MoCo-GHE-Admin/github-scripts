#!/usr/bin/env python
"""
Script to a list of teams in an org, with user lists
"""

import argparse
from getpass import getpass

from github3 import login

from github_scripts import utils


def parse_args():
    """
    Parse the command line.  Only required command is the name of the org.
    Detects if no PAT is given, asks for it.
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(
        description="Gets a list of teams and their users for an Org.  Users with '*' are maintainers of the team, reports using the team-slug"
    )
    parser.add_argument("org", help="The GH org to query", action="store", type=str)
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )

    parser.add_argument(
        "--team",
        help="The team slug to dump - if specified will ONLY use that team.  (slug, NOT name)",
    )
    parser.add_argument(
        "--unmark",
        help="Do not mark maintainers in the list",
        action="store_false",
        dest="mark_maintainer",
    )

    args = parser.parse_args()
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")

    return args


def main():
    """Get and dump out the teams for an org"""
    args = parse_args()

    gh_sess = login(token=args.token)
    org = gh_sess.organization(args.org)
    if args.team is None:
        teams = org.teams()
    else:
        teams = [org.team_by_name(args.team)]
    teamdict = {}
    for team in teams:
        userlist = []
        for maintainer in team.members(role="maintainer"):
            if args.mark_maintainer:
                name = f"*{maintainer.login}"
            else:
                name = maintainer.login
            userlist.append(name)
        for member in team.members(role="member"):
            userlist.append(member.login)
        teamdict[team.slug] = userlist

    print("Team Slug, User List")
    for teamslug, users in teamdict.items():
        userstr = ",".join(users)
        print(f'{teamslug}, "{userstr}"')


if __name__ == "__main__":
    main()

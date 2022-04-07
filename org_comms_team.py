#!/usr/bin/env python
"""
Script for creating the "comms-everyone" team in an org
This is a stopgap measure to try and communicate with people.
Unless watches are setup JUST so, people won't see this.
Mainly used prior to SAML enable/enforcement - so there's chances that
SAML will be in a splitbrain mode
"""

import argparse
from getpass import getpass

from github3 import exceptions as gh_exceptions
from github3 import login

import utils


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = argparse.ArgumentParser(
        description="Go into an org, create a team named for the --team-name and add all members to it"
    )
    parser.add_argument("org", help="organization to do this to", action="store")
    parser.add_argument(
        "--team-name",
        dest="team_name",
        help="name of the team to create, defaults to 'everybody-temp-comms'",
        action="store",
        default="everybody-temp-comms",
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


def find_team(org, team_name):
    """
    go through the organization's teams, looking for team_name if it exists,
    return the integer ID, otherwise -1
    :param org: The initialized organization object
    :param team_name: string of the team_name
    :return: integer ID if found, -1 if not.
    """
    teams = org.teams()
    for team in teams:
        if team.name == team_name:
            return team.id
    return -1


def main():
    """
    Get the args, get into GH, and create the team
    """
    args = parse_args()
    gh_sess = login(token=args.token)

    org = gh_sess.organization(args.org)

    # Let's see if the team exists
    team_found = find_team(org, args.team_name)
    if team_found > 0:
        team = org.team(team_found)
    else:
        team = org.create_team(name=args.team_name)
    member_list = org.members()
    for member in member_list:
        # Note, this call will fail if SAML is enforced, but the user isn't SAMLd.
        # This is precisely NOT the use case for this program, so "Note it and move on"
        try:
            team.add_or_update_membership(username=member.login)
            print(f"Added {member.login} to the team")
        except gh_exceptions.UnprocessableEntity:
            print(f"User {member.login} doesn't appear to be addable (SAML?) Skipping.")
    print(f"Group named {args.team_name} created in org {args.org}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script for adding a user to an org
Given a username an org, and a list of teams, send an invite to that user for the org/team
"""

from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils

# TODO: add progress bars


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = utils.GH_ArgParser(
        description="Give a username, an org, and a team list and add the user to the org.  NOTE: if the org is SAML'd you'll probably need to provision the user in your IdP system(s)"
    )
    parser.add_argument("org", type=str, help="The org to work with", action="store")
    parser.add_argument("username", help="GH user ID to add")
    parser.add_argument("--teams", help="list of team slugs", nargs="+")
    parser.add_argument("--owner", help="Should they be an owner", action="store_true")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    gh_sess = login(token=args.token)
    # First we have to convert the team names to ids
    try:
        org = gh_sess.organization(args.org)
    except gh_exceptions.NotFoundError:
        print(f"Organization {args.org} is not found")
        exit()
    try:
        user_id = gh_sess.user(args.username).id
    except gh_exceptions.NotFoundError:
        print(f"User {args.username} is not found")
        exit()
    teamlist = []
    if args.teams is not None:
        try:
            for teamslug in args.teams:
                teamlist.append(org.team_by_name(teamslug).id)
        except gh_exceptions.NotFoundError:
            print("Teams not resolving - please verify the team-slug")
            exit()
    # For some reason the module uses different terms for the member privilege if you're not adding a team
    # and also (later in the code) you'll see that it uses a different method to invite the teamless.
    if args.owner:
        priv = "admin"
    elif args.teams is not None:
        priv = "direct_member"
    else:
        priv = "member"

    try:
        if args.teams is not None:
            org.invite(team_ids=teamlist, invitee_id=user_id, role=priv)
        else:
            org.add_or_update_membership(username=args.username, role=priv)
    except Exception as error:
        print(f"An exception on creation occurred: {error}")


if __name__ == "__main__":
    main()

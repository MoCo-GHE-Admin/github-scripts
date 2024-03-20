#!/usr/bin/env python
"""
Script for removing a user/collaborator from org(s)
Given a GitHub ID, go through the list of orgs that the runner has access to
Look for orgs that the user is member of, as well as collaborator in.
Then extract and report the permissions that the user has.
"""


# from github3 import exceptions as gh_exceptions
from github3 import login
from github3.structs import GitHubIterator
from github3.users import ShortUser

from github_scripts import utils

# TODO: add progress bars


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = utils.GH_ArgParser(
        description="Given a username - go through all orgs the caller has access to, to see what the username has access to."
    )
    parser.add_argument("username", help="User to remove")
    parser.add_argument(
        "--dumpmembership",
        help="Should I look at membership in orgs, and not just collaborator status?",
        action="store_true",
        dest="membership",
    )
    args = parser.parse_args()
    return args


class OutsideCollabIterator(GitHubIterator):
    # based on work from hwine in mozilla/github-org-scripts/notebooks
    def __init__(self, org):
        super().__init__(
            count=-1,  # get all
            url=org.url + "/outside_collaborators",
            cls=ShortUser,
            session=org.session,
        )


def get_collabs(gh_sess, org):
    """
    Give me a list of all collabs in an org
    :param gh_sess: the github session
    :param org: An initialized org object
    result: list of all collabs
    """
    result = []
    for user in OutsideCollabIterator(org):
        utils.check_rate_remain(gh_sess)
        result.append(user.login.lower())
    return result


def remove_from_org_repos(gh_sess, org, user, verbose=True, dry_run=True):
    """
    Remove the user from the repos in the org
    Cycle through all repos, looking for outside collabs - noting or
    removing them as desired.
    :param gh_sess: the github session
    :param org: Initialized org object
    :param user: The GHID of the user
    :param verbose: Print out what we're doing
    :return boolean: True if we found someone.  False if no removal
    """
    if verbose:
        print(f"Looking for OCs in repos in {org.login}")
    found = False
    utils.check_rate_remain(gh_sess)
    if user in get_collabs(gh_sess, org):
        if verbose:
            print(f"\t**Found user {user} as collaborator in org {org.login}")
        found = True
    if verbose and not found:
        print(f"\t\tDid not find user {user} as an OC of any repo in {org.login}")
    return found


def main():
    """
    Start the GH connection, get the orgs, and go through them,
    chronicalling what access the username has, and report.
    """

    args = parse_args()

    gh_sess = login(token=args.token)
    utils.check_rate_remain(gh_sess)

    for org in gh_sess.organizations():
        checkit = False  # Should we check this org for specific repo perms?
        print(f"{org.login=}")
        if org.is_member(args.username):
            print("\tFound as a member!")
            if args.membership:
                checkit = True
        elif args.username in get_collabs(gh_sess, org):
            print("\tFound user collab!")
            checkit = True
        if checkit:
            print(f"Checking {org.login} for permissions for user {args.username}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script for removing a user/collaborator from org(s)
Given a username and a list of orgs, go through the orgs, and remove them as a member,
and then go through the repos, and remove them as outside collaborators.
"""

# TODO: Look at making it able to take multiple usernames on the command line

import argparse
import configparser
from getpass import getpass

# from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = argparse.ArgumentParser(
        description="Given a username - go through all orgs in the orglist.ini file and see "
        "what they need to be removed from"
    )
    parser.add_argument("username", help="User to remove")
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="*")
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    parser.add_argument(
        "--orgfile",
        help='use an ini file with the "orgs" '
        'entry with a csv list of all orgs to check, defaults to "orglist.ini"',
        action="store_const",
        const="orglist.ini",
    )
    parser.add_argument(
        "--do-it",
        # Note that the variable is "Dry Run" and it sets to True.
        # by declaring "--do-it" you flip dry run to False, and make things happen
        dest="dryrun",
        help="Actually do the removal - Otherwise just report on what you found",
        action="store_false",
        default=True,
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgfile is None:
        raise Exception("You must specify either an org or an orgfile")
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def remove_from_org_repos(gh_sess, org, user, verbose=True, dry_run=True):
    """
    Remove the user from the repos in the org
    Cycle through all repos, looking for outside collabs - noting or
    removing them as desired.
    :param gh_sess: the github session
    :param org: Initialized org object
    :param user: The GHID of the user
    :param verbose: Print out what we're doing
    :param dry_run: Boolean, if true don't DO anything
    :return boolean: True if we found someone.  False if no removal
    """
    print(f"Looking for OCs in repos in {org.login}")
    found = False
    repolist = org.repositories()
    utils.check_rate_remain(gh_sess)
    for repo in repolist:
        utils.check_rate_remain(gh_sess)
        if repo.is_collaborator(user):
            print(f"\t**Found user {user} as collaborator in repo {repo.name}")
            found = True
            if not dry_run:
                print(f"\t***Removing user {user} as collaborator from repo {repo.name}")
                if not repo.remove_collaborator(user):
                    raise Exception(f"Failed to remove {user} from repo {repo.name}")
    if not found:
        print(f"\t\tDid not find user {user} as an OC of any repo in {org.login}")
    return found


def remove_from_org(gh_sess, org, user, verbose=True, dry_run=True):
    """
    Remove the user from the org.
    :param gh_sess: the github session
    :param org: Initialized org object
    :param user: The GHID of the user
    :param verbose: Print out what we're doing
    :param dry_run: Boolean, if true don't DO anything
    :return boolean: True if we found someone.  False if no removal
    """
    print(f"Looking for members in org {org.login}")
    found = False
    if org.is_member(user):
        utils.check_rate_remain(gh_sess)
        print(f"\t**Found user {user} in org {org.login}")
        found = True
        if not dry_run:
            print(f"\t***Removing user {user} from org {org.login}")
            if not org.remove_member(user):
                raise Exception(f"Failed to remove {user} from org {org.login}")
    if not found:
        print(f"\t\tDid not find member {user} in org {org.login}")
    return found


def main():
    """
    Start the GH connection, get the orgs, and go through them,
    removing members, and scanning outside collaborators
    """
    pass
    args = parse_args()

    orglist = []
    if args.orgfile is not None:
        config = configparser.ConfigParser()
        config.read(args.orgfile)
        orglist = config["GITHUB"]["orgs"].split(",")
    else:
        orglist = args.orgs

    gh_sess = login(token=args.token)
    utils.check_rate_remain(gh_sess)
    found_orgs = []
    # TODO: iterate over listed orgs and pull the user from them
    for orgname in orglist:
        org = gh_sess.organization(orgname)
        if not remove_from_org(gh_sess, org, args.username, dry_run=args.dryrun):
            # you can't be a member and a collab - so not a member, check collab
            remove_from_org_repos(gh_sess, org, args.username, dry_run=args.dryrun)
        else:
            found_orgs.append(org.login)
    if len(found_orgs) > 0:
        print(f"Found user {args.username} as a member of these orgs: {found_orgs}")

    # Look here for API usage: https://docs.github.com/en/rest/reference/orgs#remove-outside-collaborator-from-an-organization


if __name__ == "__main__":
    main()

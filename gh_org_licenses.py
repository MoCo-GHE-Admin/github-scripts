#!/usr/bin/env python
"""
Script to calculate license count for GHE give a list of ORGs

Licenses:
Members of orgs take a license
Outside collaborators with ANY access (even just read) to a private repo take a license.

"""

import argparse
import configparser
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

from github3 import exceptions as gh_exceptions
from github3 import login

import utils


def parse_arguments():
    """
    Get a list of orgs (either in CLI or in INI file)
    Get the PAT (either via command line or toml file)
    """
    parser = argparse.ArgumentParser(
        description="Provided a list of orgs, output how many GHE licenses are required."
    )
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="*")
    parser.add_argument("--pending", help="Include Pending requests?", action="store_true")
    parser.add_argument(
        "--orgini",
        help='use "orglist.ini" with the "orgs" ' "entry with a csv list of all orgs to check",
        action="store_const",
        const="orglist.ini",
    )
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgini is None:
        raise Exception("You must specify either an org or an orgini")
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def check_rate_remain(gh_sess, loopsize=5):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: Should we print a progress element to stderr
    """
    # TODO: Look at making the naptime show that you're still making progress
    while gh_sess.ratelimit_remaining < loopsize:
        # Uh oh.
        # calculate how long to sleep, sleep that long.
        refreshtime = datetime.fromtimestamp(gh_sess.rate_limit()["resources"]["core"]["reset"])
        now = datetime.now()
        naptime = (refreshtime - now).seconds
        print(f"Sleeping for {naptime} seconds", file=sys.stderr)
        sleep(naptime)


def org_members_set(org, pending):
    """
    :param org: Initialized GH org
    :param pending: boolean if we are to include pending invites
    :result: Set of the members of this org
    """
    member_list = org.members()
    result_set = set()
    try:
        for member in member_list:
            result_set.add(member.login)
            check_rate_remain(org, loopsize=5)
        if pending:
            for invite in org.invitations():
                check_rate_remain(org, loopsize=5)
                # print(f"found invites for {org.name=}")
                if invite.login is None:
                    result_set.add(invite.email)
                else:
                    result_set.add(invite.login)
    except gh_exceptions.ForbiddenError:
        print(f"You don't have admin access to org {org.name} to view invitations")
    return result_set


def org_oc_set(org, pending):
    """
    :param org: Initialized GH org
    :param pending: boolean if we are to include pending invites
    :result: Set of the OCs with private repo priv in this org

    Note, we have to go through ALL the repos - while "internal" repos
    show as "private" when asked, asking for all "private" repos does
    not return internal repos.
    """
    oc_set = set()
    # repo_set = set()
    repo_list = org.repositories()
    for repo in repo_list:
        try:
            if repo.private:
                # repo_set.add(repo.name)
                for collab in repo.collaborators(affiliation="outside"):
                    oc_set.add(collab.login)
                    check_rate_remain(org, loopsize=5)
            if pending:
                for invite in repo.invitations():
                    check_rate_remain(org, loopsize=5)
                    oc_set.add(invite.invitee.login)
                    print(f"{repo.name=} has an invite for {invite.invitee.login}")
        except gh_exceptions.NotFoundError:
            # If this is a ghsa - this is expected, else scream and shout
            if repo.name.find("-ghsa-") == -1:
                raise gh_exceptions.NotFoundError()

    # print(f"list of private repos {repo_set}")
    return oc_set


def main():
    """
    Connect to GH
    Get the list of Orgs, start parsing things.
    We're gonna use sets to make things easy, seeing as how they dedupe themselves.
    """
    overallset = set()
    args = parse_arguments()
    # Read in the config if there is one
    orglist = []
    if args.orgini is not None:
        config = configparser.ConfigParser()
        config.read(args.orgini)
        orglist = config["GITHUB"]["orgs"].split(",")
    else:
        orglist = args.orgs

    gh_sess = login(token=args.token)
    for org in orglist:
        init_org = gh_sess.organization(org)
        org_set = org_members_set(init_org, args.pending)
        oc_set = org_oc_set(init_org, args.pending)

        print(f"ORG: {org}: Members: {len(org_set)}, OC: {len(oc_set)}")

        # union of overallset with the org_set and oc_set
        overallset |= org_set | oc_set
        print(f"Current overall license count: {len(overallset)}")
        # print(f"{org=}, {oc_set=}")
        # print(f"Set List: {overallset}")
    print(f"Final count: {len(overallset)}")


if __name__ == "__main__":
    main()

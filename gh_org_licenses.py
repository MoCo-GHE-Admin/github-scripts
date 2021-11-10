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


def _create_char_spinner():
    """
    Creates a generator yielding a char based spinner.
    """
    while True:
        for char in "|/-\\":
            yield char


_spinner = _create_char_spinner()


def spinner(label=""):
    """
    Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stderr.write("\r%s %s" % (label, next(_spinner)))
    sys.stderr.flush()


def check_rate_remain(gh_sess, loopsize=100, update=True):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: should we print things letting you know what we're doing?
    Note, we always print the "sleeping for XXX seconds"
    """
    # TODO: Look at making the naptime show that you're still making progress
    while gh_sess.rate_limit()["resources"]["core"]["remaining"] < loopsize:
        # Uh oh.
        # calculate how long to sleep, sleep that long.
        refreshtime = datetime.fromtimestamp(gh_sess.rate_limit()["resources"]["core"]["reset"])
        now = datetime.now()
        naptime = (refreshtime - now).seconds + 120
        print(f"API limits exhausted - sleeping for {naptime} seconds", file=sys.stderr)
        for timer in range(naptime):
            sleep(1)
            if update:
                spinner()
        if update:
            print(file=sys.stderr)


def org_members_set(gh_sess, org_name, pending):
    """
    :param gh_sess: initialized github object
    :param org_name: Name of a GH org
    :param pending: boolean if we are to include pending invites
    :result: Set of the members of this org
    """
    org = gh_sess.organization(org_name)
    member_list = org.members()
    result_set = set()
    try:
        for member in member_list:
            result_set.add(member.login)
            check_rate_remain(gh_sess)
        if pending:
            for invite in org.invitations():
                check_rate_remain(gh_sess)
                if invite.login is None:
                    result_set.add(invite.email)
                else:
                    result_set.add(invite.login)
    except gh_exceptions.ForbiddenError:
        print(f"You don't have admin access to org {org.name} to view invitations")
    return result_set


def org_oc_set(gh_sess, org_name, pending):
    """
    :param gh_sess: initialized github object
    :param org_name: Name of a GH org
    :param org: Initialized GH org
    :param pending: boolean if we are to include pending invites
    :result: Set of the OCs with private repo priv in this org

    Note, we have to go through ALL the repos - while "internal" repos
    show as "private" when asked, asking for all "private" repos does
    not return internal repos.
    """
    org = gh_sess.organization(org_name)
    oc_set = set()
    # repo_set = set()
    repo_list = org.repositories()
    for repo in repo_list:
        try:
            if repo.private:
                # We're in a private repo - get me all OC's
                for collab in repo.collaborators(affiliation="outside"):
                    oc_set.add(collab.login)
                    check_rate_remain(gh_sess)
                if pending:
                    # Get me all invites to the private repo
                    for invite in repo.invitations():
                        check_rate_remain(gh_sess)
                        oc_set.add(invite.invitee.login)
        except gh_exceptions.NotFoundError:
            # If this is a ghsa - this is expected, else scream and shout
            if repo.name.find("-ghsa-") == -1:
                raise gh_exceptions.NotFoundError()

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
    # Check the API rate remaining before starting.
    check_rate_remain(gh_sess)

    # Go through every org given
    for org in orglist:
        # Get a set (naturally deduped) of members
        org_set = org_members_set(gh_sess, org, args.pending)
        # Get a set (naturally deduped) of private OCs
        oc_set = org_oc_set(gh_sess, org, args.pending)

        print(f"ORG: {org}: Members: {len(org_set)}, OC: {len(oc_set)}")

        # union of overallset with the org_set and oc_set
        overallset |= org_set | oc_set
        print(f"Current overall license count: {len(overallset)}")
    print(f"Final count: {len(overallset)}")


if __name__ == "__main__":
    main()

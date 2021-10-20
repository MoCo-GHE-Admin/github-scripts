#!/usr/bin/env python
"""
Script to perform a search of supplied orgs, returning the repo list that return positives
"""

import argparse
import configparser
import sys
from getpass import getpass
from time import sleep

from github3 import exceptions as gh_exceptions
from github3 import login


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(
        description="Get file search resuls for an org, returning repo list.  "
        "e.g. if you want 'org:<ORGNAME> filename:<FILENAME> <CONTENTS>', "
        "then you just need 'filename:<FILENAME> <CONTENTS>' "
        "and then list the orgs to apply it to.  "
        "Note: There's a pause of ~10 seconds between org searches "
        "due to GitHub rate limits - add a -v if you want notice printed that it's waiting"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="The query to run, without orgs",
        action="store",
        required=True,
    )
    parser.add_argument(
        "orgs", type=str, help="The org to work on", action="store", nargs="*"
    )
    parser.add_argument(
        "--orgini",
        help='use "orglist.ini" with the "orgs" '
        "entry with a csv list of all orgs to check",
        action="store_const",
        const="orglist.ini",
    )
    parser.add_argument(
        "--token", help="github token with perms to examine your org", action="store"
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        help="Verbose - Print out that we're waiting for rate limit reasons",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-t",
        dest="time",
        default=10,
        type=int,
        help="Time to sleep between searches, in seconds, should be 10s or more",
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgini is None:
        raise Exception("You must specify either an org or an orgini")
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def main():
    """
    Taking in the query and list of orgs, run the search,
    print out the org name and the list of repos affected.
    """
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
    length = len(orglist)  # Used to determine when to pause
    for org in orglist:
        try:
            search = gh_sess.search_code(f"org:{org} {args.query}")
            repos = set()
            for result in search:
                repos.add(result.repository.name)
            print(f'org: {org} Repo: {",".join(repos)}')
        except gh_exceptions.UnprocessableEntity:
            print(f"org: {org} Failed, likely due to lack of repos in the org")
        finally:
            length -= 1
            if length > 0:
                if args.verbose:
                    print(
                        f"Sleeping {args.time} seconds per GitHub's secondary rate limits",
                        file=sys.stderr,
                    )
                # per https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-secondary-rate-limits
                sleep(args.time)


if __name__ == "__main__":
    main()

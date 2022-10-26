#!/usr/bin/env python
"""
Check remaining API calls, and time of next reset
"""

import argparse
from datetime import datetime
from getpass import getpass

from github3 import login

from github_scripts import utils


def parse_args():
    """
    Parse the args - need either the username adn token, or the config to exist
    return the parsed args.
    """
    parser = argparse.ArgumentParser(
        description="Print out the remaining API limits, and the time of the reset"
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


def main():
    """
    Check the remaining rate for the user, printing out the levels, as well as time of next reset
    """
    args = parse_args()
    gh_sess = login(token=args.token)
    rates = gh_sess.rate_limit()
    limit_remain = rates["resources"]["core"]["remaining"]
    refreshtime = datetime.fromtimestamp(rates["resources"]["core"]["reset"])
    print(f"Remaining limits: {limit_remain}, which will reset at {refreshtime}")
    searchlimit = rates["resources"]["search"]["remaining"]
    searchrefresh = datetime.fromtimestamp(rates["resources"]["search"]["reset"])
    print(f"Remaining search limits: {searchlimit}, which will reset at {searchrefresh}")


if __name__ == "__main__":
    main()

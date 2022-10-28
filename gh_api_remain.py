#!/usr/bin/env python
"""
Check remaining API calls, and time of next reset
"""

from datetime import datetime

from github3 import login

from github_scripts import utils


def parse_args():
    """
    Parse the args - need either the username adn token, or the config to exist
    return the parsed args.
    """
    parser = utils.GH_ArgParser(
        description="Print out the remaining API limits, and the time of the reset"
    )
    args = parser.parse_args()
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

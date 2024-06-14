#!/usr/bin/env python
"""
Script to list the organizations that the runner belongs to.
"""

from github3 import login

from github_scripts import utils


def parse_args():
    """
    Parse the command line.
    Detects if no PAT is given, asks for it.
    :return: Returns the parsed CLI datastructures.
    """

    parser = utils.GH_ArgParser(
        description="Gets a list of the organizations that the user belongs to.  Useful as input to scripts that take a list of orgs.  Note if you have personal orgs, this will be included."
    )
    args = parser.parse_args()

    return args


def main():
    """Get the list of orgs"""
    args = parse_args()

    gh_sess = login(token=args.token)
    for org in gh_sess.organizations():
        print(org.login)


if __name__ == "__main__":
    main()

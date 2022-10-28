#!/usr/bin/env python
"""
Script to generate a list of owners of all orgs - with the orgs they own.
"""

import configparser

from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(description="Look at orgs, and get the list of owners")
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="*")
    parser.add_argument(
        "--orgini",
        help='use "orglist.ini" with the "orgs" ' "entry with a csv list of all orgs to check",
        action="store_const",
        const="orglist.ini",
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgini is None:
        raise Exception("You must specify either an org or an orgini")
    return args


def main():
    """
    Open the connection to github, and start looking at the owners
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
    ownerdict = {"Owner GHName": ["Orgs Owned"]}
    # Go through the list of orgs
    for orgname in orglist:
        # print(f'look at {orgname=}')
        org = gh_sess.organization(orgname)
        # Get a list of all admin (owners) for the org
        ownerlist = org.members(role="admin")
        # Add the owner as the key to the dict,
        # and add the org to the set of repos.
        for owner in ownerlist:
            if owner.login in ownerdict:
                ownerdict[owner.login].add(orgname)
            else:
                ownerdict[owner.login] = set()
                ownerdict[owner.login].add(orgname)

    for key, val in ownerdict.items():
        orgstr = ""
        count = len(val)
        for item in val:
            orgstr += f"{item}"
            if count != 1:  # This is NOT the last item
                orgstr += ","
            count -= 1
        print(f"{key}:{orgstr}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script to generate a list of owners of all orgs - with the orgs they own.
"""

from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(description="Look at orgs, and get the list of owners")
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="+")
    args = parser.parse_args()
    return args


def main():
    """
    Open the connection to github, and start looking at the owners
    """
    args = parse_arguments()
    # Read in the config if there is one

    gh_sess = login(token=args.token)
    ownerdict = {"Owner GHName": ["Orgs Owned"]}
    # Go through the list of orgs
    for orgname in args.orgs:
        # print(f'look at {orgname=}')
        try:
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
        except gh_exceptions.NotFoundError:
            print(f"Org {orgname} not found - continuing with remaining orgs")

    for key, val in ownerdict.items():
        orgstr = ""
        count = len(val)
        for item in val:
            orgstr += f"{item}"
            if count != 1:  # This is NOT the last item
                orgstr += ","
            count -= 1
        print(f"{key}: {orgstr}")


if __name__ == "__main__":
    main()

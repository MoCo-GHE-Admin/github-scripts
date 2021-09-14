#!/usr/bin/env python
"""
Script to perform a search of supplied orgs, returning the repo list that return positives
"""

import argparse
from getpass import getpass
# import sys
from github3 import login

def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(description=
        "Get file search resuls for an org, returning repo list.  "
        "e.g. if you want 'org:<ORGNAME> filename:<FILENAME> <CONTENTS>' "
        "Then you just need 'filename:<FILENAME> <CONTENTS>' and then list the orgs to apply it to")
    parser.add_argument('--query', type=str, help="The query to run, without orgs",
                        action='store', required=True)
    parser.add_argument('orgs', type=str, help="The org to work on",
                        action='store', nargs='+')
    parser.add_argument('--token', help='github token with perms to examine your org',
                        action='store')
    args = parser.parse_args()
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args



def main():
    """
    Taking in the query and list of orgs, run the search,
    print out the org name and the list of repos affected.
    """
    args = parse_arguments()
    gh_sess = login(token=args.token)

    for org in args.orgs:
        search = gh_sess.search_code(f'org:{org} {args.query}')
        repos = []
        for result in search:
            repos.append(result.repository.name)
        print(f'org: {org} Repo: {",".join(repos)}')


if __name__ == '__main__':
    main()

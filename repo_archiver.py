#!/usr/bin/env python
"""
Script for archiving repo
Takes an Owner/repo and does the following
Creates a label "ARCHIVED" in red (or specified)
Applies that label to all open issues and PR's
prepends "DEPRECATED - " to the description
Archives the repo
"""

import argparse
import sys
from getpass import getpass
from github3 import login
from github3 import exceptions as gh_exceptions

def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = argparse.ArgumentParser(description=
        "Archive the specified repo, closing out issues and PRs")
    parser.add_argument('repos', help = "owner/repo to archive", nargs = '*', action = 'store')
    parser.add_argument('--token', help = "PAT to access github.  Needs Write access to the repos",
                        action='store')
    parser.add_argument('--file', help = 'File with "owner/repo" one per line to archive',
                        action = 'store')
    parser.add_argument("--force", help="Don't stop if you detect previous archivers",
                        action='store_true')
    parser.add_argument('-q', help = 'DO NOT print, or request confirmations', dest = 'quiet',
                        action='store_true', default = False)
    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args


def main():
    """
    Main logic for the archiver
    """
    args = parse_args()
    gh_sess = login(token = args.token)

    repolist = []
    if args.repos != []:
        repolist = args.repos
    else:
        # Rip open the file, make a list
        txtfile = open(args.file, 'r')
        repolist = txtfile.readlines()
        txtfile.close()

    for orgrepo in repolist:
        try:
            org = orgrepo.split('/')[0].strip()
            repo = orgrepo.split('/')[1].strip()
        except IndexError:
            print(f'{orgrepo} needs to be in the form ORG/REPO')
            sys.exit()
        try:
            gh_repo = gh_sess.repository(owner = org, repository = repo)
        except gh_exceptions.NotFoundError:
            print(f'Trying to open {org=}, {repo=}, failed with 404')
            sys.exit()
        if not args.quiet:
            print(f'working with repo: {gh_repo.name}')
            print('\tcreating archive label')
        labellist = gh_repo.labels()

        need_flag = True
        for label in labellist:
            if label.name == "ARCHIVED":
                need_flag = False
                if not args.force:
                    print('Uh oh.  ARCHIVED label already exists?  Closing out so I don''t '
                        'step on other processes')
                    sys.exit()
        if need_flag:
            gh_repo.create_label(name = "ARCHIVED", color = '#c41a1a',
                            description = "CLOSED at time of archiving")
        if not args.quiet:
            print('\tStarting work on issues')
        issues = gh_repo.issues(state = 'open')
        #Need to do two passes - if we do one pass, the closure erases the label
        for issue in issues:
            #update label
            issue.add_labels('ARCHIVED')
        for issue in issues:
            try:
                issue.close()
                if not args.quiet:
                    print(f'\tLabeled and closed issue: {issue.title}')
            except gh_exceptions.UnprocessableEntity:
                print(f"Got 422 Unproccessable on issue {issue.title},"
                    " continuing.  May need to run --force or manually finish closing.")
        topics = gh_repo.topics().names
        topics.append('abandoned')
        topics.append('unmaintained')
        gh_repo.replace_topics(topics)
        if not args.quiet:
            print('\tUpdated topics')
        description = gh_repo.description
        if description is not None:
            description = 'DEPRECATED - ' + description
        else:
            description = 'DEPRECATED'
        gh_repo.edit(name = gh_repo.name, description = description, archived = True)
        if not args.quiet:
            print(f'\tUpdated description and archived the repo {repo}')

if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
Script for getting various org based statistics out of github.
"""

import argparse
import time
import sys
from datetime import datetime
from getpass import getpass
from github3 import login

def _create_char_spinner():
    """Creates a generator yielding a char based spinner.
    """
    while True:
        for char in '|/-\\':
            yield char


_spinner = _create_char_spinner()


def spinner(label=''):
    """Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stderr.write("\r%s %s" % (label, next(_spinner)))
    sys.stderr.flush()

def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """

    parser = argparse.ArgumentParser(description="Get stats out of github about repos\n"\
        "Note that the dates are 'end of week' and "\
        "the latest you should see for commits is last Saturday")
    parser.add_argument('operation', choices=['repoactive', 'orgactive'],
                        action='store')
    parser.add_argument('org', help="owner or org of the repo",
                        action='store', type=str)
    parser.add_argument('--repo', type=str, help='the repo to act upon',
                        action='store')
    parser.add_argument('--token', help='github token with perms to examine your repo',
                        action='store')
    parser.add_argument('--admin-only', help='for user and teams, only show admins',
                        default=False, action='store_true')
    parser.add_argument('--delay', help='Seconds to delay between lookups to avoid throttling '
                        'if you see errors around 202 status, increase this number',
                        action='store', type=float, default=0.5, dest='delay')
    args = parser.parse_args()
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def activity(gh_sess, org, delay=0.5, printout=True):
    """
    go through the org and return a list of repos, with the date of their latest commit,
        or no commit, for the last year
    :param gh_sess: an initialized github session
    :param org: the organization (or owner) name
    :param delay: Time between lookups - Github throttles
    :param printout: Print it out here - defaults True, if False, just return the list.
    :return: list, repo, created_date, last admin update, last push, last commit
    """
    repolist = gh_sess.repositories_by(org)
    commitlist = {}
    for short_repo in repolist:
        repo = short_repo.refresh()
        topdate = 0
        commits = repo.commit_activity()
        for week in commits:
            if week['total'] != 0:
                if week['week'] > topdate:
                    topdate = week['week']
        time.sleep(delay)  # Waiting for Github to not ratelimit
        spinner()
        commitval = 0
        if topdate == 0:
            #no commits found, update list as apropos
            commitval = 'None'
        else:
            commitval = datetime.fromtimestamp(topdate)
        commitlist[repo.name] = {'created_at':repo.created_at,
                                'updated_at':repo.pushed_at,
                                'admin_update':repo.updated_at,
                                'last_commit': commitval,
                                'archived':repo.archived}
    if printout:
        print()
        print("Repo, Created, Updated, Admin_update, Last_commit")
        for repo in commitlist:
            if commitlist[repo]['archived']:
                print(f"{repo}, ARCHIVED")
            else:
                print(f"{repo},{commitlist[repo]['created_at']},{commitlist[repo]['updated_at']},"
                        f"{commitlist[repo]['admin_update']},{commitlist[repo]['last_commit']}")
    return commitlist

def repo_activity(gh_sess, org, repo, printout=True):
    """
    Look at the repo, and return activity, with the date of their latest commit,
        or no commit, over the last year
    :param gh_sess: an initialized github session
    :param org: the organization (or owner) name
    :param repo: the repo name
    :param printout: Print it out here - defaults True, if False, just return the list.
    :return: list, repo, created_date, last admin update, last push, last commit
    """
    short_repo = gh_sess.repository(org, repo)

    commitlist = {}
    repo = short_repo.refresh()
    topdate = 0
    commits = repo.commit_activity()
    for week in commits:
        if week['total'] != 0:
            if week['week'] > topdate:
                topdate = week['week']
    commitval = 0
    if topdate == 0:
        #no commits found, update list as apropos
        commitval = 'None'
    else:
        commitval = datetime.fromtimestamp(topdate)
    commitlist[repo.name] = {'created_at':repo.created_at,
                            'updated_at':repo.pushed_at,
                            'admin_update':repo.updated_at,
                            'last_commit': commitval,
                            'archived':repo.archived}

    if printout:
        print("Repo, Created, Updated, Admin_update, Last_commit")
        for repo in commitlist:
            if commitlist[repo]['archived']:
                print(f"{repo}, ARCHIVED")
            else:
                print(f"{repo},{commitlist[repo]['created_at']},{commitlist[repo]['updated_at']},"
                        f"{commitlist[repo]['admin_update']},{commitlist[repo]['last_commit']}")
    return commitlist



def main():
    """
    Main function for github repo_stats
    """
    args = parse_arguments()
    gh_session = login(token=args.token)

    # Figure out which option is called, and DO the thing
    if args.operation == 'orgactive':
        activity(gh_session, args.org, delay=args.delay)
    elif args.operation == 'repoactive':
        print(f'sess: {gh_session}, org: {args.org}, repo: {args.repo}')
        repo_activity(gh_session, args.org, args.repo)



if __name__ == '__main__':
    main()

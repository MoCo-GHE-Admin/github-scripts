#!/usr/bin/env python
"""
Script for determining activity levels of a repo
Used to help determination for archiving/moving repos that aren't active
"""

import argparse
from getpass import getpass
from datetime import datetime
from github3 import login
from github3 import exceptions as gh_exceptions

def parse_args():
    """
    Parse the command line.  Required commands is the name of the "org/repo"
    Will accept many repos on the command line, and they can be in different orgs
    Also can take the output in a file.  one "org/repo" per line
    Detects if no PAT is given, asks for it.
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(description=
                    "Gets a latest activity for a repo or list of repos")
    parser.add_argument('repos',
                    help='list of repos to examine',
                    action='store', nargs='*')
    parser.add_argument('--token', help='github token with perms to examine your repo',
                    action='store')
    parser.add_argument('--file', help="File of repo names, 1 per line",
                    action = 'store')

    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def repo_activity(gh_sess, org, repo, printout=True, header=True):
    """
    Look at the repo, and return activity, with the date of their latest commit,
        or no commit, over the last year
    :param gh_sess: an initialized github session
    :param org: the organization (or owner) name
    :param repo: the repo name
    :param printout: Print it out here - defaults True, if False, just return the list.
    :param header: Should I print a descriptive header?
    :return: list, repo, created_date, last admin update, last push, last commit
    """
    short_repo = gh_sess.repository(org, repo)

    commitlist = {}
    repo = short_repo.refresh()
    topdate = 0
    commits = repo.commit_activity()
    # Look through the last year of commit activity
    # for each week, see if there's any commits
    # if there is, and it's a more recent week than we have recorded, record it.
    # (some returns from the commit_activity are out of order, hence
    # we can't just look at the last active week and assume it's the mose recent)
    try:
        for week in commits:
            if week['total'] != 0:
                if week['week'] > topdate:
                    topdate = week['week']
        commitval = 0
    except gh_exceptions.UnexpectedResponse:
        commitval = "Unexpected, possibly empty repo"
    if (commitval == 0 and topdate == 0):
        #no commits found, update list as apropos
        commitval = 'None'
    elif topdate != 0:
        commitval = datetime.fromtimestamp(topdate)
    commitlist[repo.name] = {'created_at':repo.created_at,
                            'updated_at':repo.pushed_at,
                            'admin_update':repo.updated_at,
                            'last_commit': commitval,
                            'archived':repo.archived}

    if printout:
        if header:
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
    Given a list of repos, and an org, get some data around last use
    """

    args = parse_args()

    header = True
    repolist = []
    if args.repos != []:
        repolist = args.repos
    else:
        # Rip open the file, make a list
        txtfile = open(args.file, 'r')
        repolist = txtfile.readlines()
        txtfile.close()

    gh_sess = login(token=args.token)

    for orgrepo in repolist:
        org = orgrepo.split('/')[0].strip()
        repo = orgrepo.split('/')[1].strip()
        repo_activity(gh_sess, org, repo, header=header)
        if header:
            header = False #We only want a header on the first line

if __name__ == '__main__':
    main()

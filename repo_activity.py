#!/usr/bin/env python
"""
Script for determining activity levels of a repo
Used to help determination for archiving/moving repos that aren't active
"""

import argparse
import sys
from time import sleep
from getpass import getpass
from datetime import datetime
from github3 import login
from github3 import exceptions as gh_exceptions

MAX_RETRIES = 5

def parse_args():
    """
    Parse the command line.  Required commands is the name of the "org/repo"
    Will accept many repos on the command line, and they can be in different orgs
    Also can take the output in a file.  one "org/repo" per line
    Detects if no PAT is given, asks for it.
    And finally a delay for in between calls - defaults to 0.1 seconds
    Used to rate limit so we don't get 202 for stats calls.
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(description=
                    "Gets a latest activity for a repo or list of repos")
    parser.add_argument('repos',
                    help = 'list of repos to examine',
                    action = 'store', nargs='*')
    parser.add_argument('--token', help='github token with perms to examine your repo',
                    action = 'store')
    parser.add_argument('--delay',
                    help = 'Default time between calls - defaults so that you can''t overrun',
                    action = 'store', default=4.5, type=float)
    parser.add_argument('--file', help = "File of repo names, 1 per line",
                    action = 'store')

    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def repo_activity(gh_sess, org, repo, header=True):
    """
    Look at the repo, and return activity, with the date of their latest commit,
        or no commit, over the last year
    :param gh_sess: an initialized github session
    :param org: the organization (or owner) name
    :param repo: the repo name
    :param header: Should I print a descriptive header?
    :return: Status code of the commits iterator for retry purposes.
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
    # TODO BEFORE checking weekly - check  the commits.last_status for 202 - retry if you get
    status_code = commits.last_status
    try:
        first = True
        for week in commits:
            # print(f'Result: {commits.last_status}, repo: {repo.name}', file = sys.stderr)
            if first:
                status_code = commits.last_status
                # print(f'Result: {commits.last_status}, response: {commits.last_response}, repo: {repo.name}', file = sys.stderr)
                if status_code == 202:
                    return status_code
                first = False
            if week['total'] != 0:
                if week['week'] > topdate:
                    topdate = week['week']
        commitval = 0
    except gh_exceptions.UnexpectedResponse:
        # print(f'UNEXPECTED: Result: {commits.last_status}, response: {commits.last_response}, repo: {repo.name}', file = sys.stderr)
        commitval = "Unexpected, possibly empty repo"
    except gh_exceptions.NotFoundError:
        # print(f'NOTFOUND: Result: {commits.last_status}, response: {commits.last_response}, repo: {repo.name}', file = sys.stderr)
        commitval = "Unexpected, possibly temp repo"
    except gh_exceptions.ForbiddenError as forbidden_Error:
        # print(f'FORBIDDEN: Result: {commits.last_status}, response: {commits.last_response}, repo: {repo.name}', file = sys.stderr)
        raise Exception('Forbidden error, likely overran rate limiting ' + forbidden_Error.message)
    finally:
        status_code = commits.last_status
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

    if header:
        print("Repo, Created, Updated, Admin_update, Last_commit")
    for repo in commitlist:
        if commitlist[repo]['archived']:
            print(f"{repo}, ARCHIVED")
        else:
            print(f"{repo},{commitlist[repo]['created_at']},{commitlist[repo]['updated_at']},"
                    f"{commitlist[repo]['admin_update']},{commitlist[repo]['last_commit']}")
    return status_code

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
        done = False
        count = 0
        while not done:
            #TODO: Thanks to this, we add up to 5 lines to the file for a 202-failed point.  
            count += 1
            result = repo_activity(gh_sess, org, repo, header=header)
            if result != 202 or count >= MAX_RETRIES:
                # print(f'Leaving Loop - result: {result}, done: {done}, count: {count}, repo: {repo}', file = sys.stderr)
                if count == MAX_RETRIES and result == 202:
                    # We errored out --- put in something in the output to that effect.
                    print(f'{org}/{repo},GH Gave 202 Error')
                    print(f'{org}/{repo},GH Gave 202 Error '
                        f'- failed out after {MAX_RETRIES} attempts.',
                        file = sys.stderr)
                done = True
            if header:
                header = False #We only want a header on the first line
            sleep(args.delay)
            if result == 202:
                sleep(10)

if __name__ == '__main__':
    main()

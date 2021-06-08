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
#Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 6

def _create_char_spinner():
    """
    Creates a generator yielding a char based spinner.
    """
    while True:
        for char in '|/-\\':
            yield char


_spinner = _create_char_spinner()

def spinner(label=''):
    """
    Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stderr.write("\r%s %s" % (label, next(_spinner)))
    sys.stderr.flush()

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
                    help = 'list of repos to examine - or use --file for file base input',
                    action = 'store', nargs='*')
    parser.add_argument('--token', help='github token with perms to examine your repo',
                    action = 'store')
    parser.add_argument('--file', help = "File of 'owner/repo' names, 1 per line",
                    action = 'store')
    parser.add_argument('-i', action = 'store_true', default = False, dest = 'info',
                    help = 'Give visual output of that progress continues - '
                    'useful for long runs redirected to a file')
    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def check_rate_remain(gh_sess, loopsize, update=False):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.  
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: Should we print a progress element to stderr
    """
    while gh_sess.rate_limit()['resources']['core']['remaining'] < loopsize:
        # Uh oh.
        if update:
            sleep(5)
            spinner()
        else:
            #calculate how long to sleep, sleep that long.
            refreshtime = datetime.fromtimestamp(
                gh_sess.rate_limit()['resources']['core']['reset'])
            now = datetime.now()
            naptime = (refreshtime-now).seconds
            print(f'Sleeping for {naptime} seconds', file=sys.stderr)
            sleep(naptime)

def repo_activity(gh_sess, org, repo, header=True): # pylint: disable=too-many-branches
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
    # we can't just look at the last active week and assume it's the most recent)

    # Note: Repos with LOTS of activity (gecko-dev for one) are SO busy that commit
    # stats for them will ALWAYS return a 202.  This is basically expected.
    status_code = commits.last_status
    try:
        first = True
        for week in commits:
            # print(f'Result: {commits.last_status}, repo: {repo.name}', file = sys.stderr)
            if first:
                status_code = commits.last_status
                # print(f'Result: {commits.last_status}, response: '
                #       f'{commits.last_response}, repo: {repo.name}', file = sys.stderr)
                if status_code == 202:
                    return status_code
                first = False
            if week['total'] != 0:
                if week['week'] > topdate:
                    topdate = week['week']
        commitval = 0
    except gh_exceptions.UnexpectedResponse:
        # print(f'UNEXPECTED: Result: {commits.last_status}, response: '
        #       f'{commits.last_response}, repo: {repo.name}', file = sys.stderr)
        commitval = "Unexpected, possibly empty repo"
    except gh_exceptions.NotFoundError:
        # print(f'NOTFOUND: Result: {commits.last_status}, response: '
        #       f'{commits.last_response}, repo: {repo.name}', file = sys.stderr)
        commitval = "Unexpected, possibly temp repo"
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
            # Note: we add up to 5 lines
            #       to the file for a 202-failed point.
            #       Given the structure, it's unclear how to fix, and it's rare
            count += 1
            result = repo_activity(gh_sess, org, repo, header=header)
            if result != 202 or count >= MAX_RETRIES:
                # print(f'Leaving Loop - result: {result}, '
                #       f'done: {done}, count: {count}, repo: {repo}', file = sys.stderr)
                if count == MAX_RETRIES and result == 202:
                    # We errored out --- put in something in the output to that effect.
                    print(f'{org}/{repo},GH Gave 202 Error')
                    print(f'{org}/{repo},GH Gave 202 Error '
                        f'- failed out after {MAX_RETRIES} attempts.',
                        file = sys.stderr)
                done = True
            if header:
                header = False #We only want a header on the first line
            check_rate_remain(gh_sess, RATE_PER_LOOP, args.info)

            if result == 202:
                sleep(10)
            if args.info:
                spinner()

if __name__ == '__main__':
    main()

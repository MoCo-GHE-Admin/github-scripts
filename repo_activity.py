#!/usr/bin/env python
"""
Script for determining activity levels of a repo
Going through the last years of commits for the last active week
And barring that reporting the github updated_at which might be much earlier than
a year.  And finally created_at so we know who old things are.

Used to help determination for archiving/moving repos that aren't active
"""

import argparse
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

from github3 import exceptions as gh_exceptions
from github3 import login

import utils

# Some repos that have LOTS of traffic (mozilla/gecko-dev) will ALWAYS fail on getting the stats
# This is the number of retries, otherwise, just report the problem in the output and move along
MAX_RETRIES = 5
# Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 20


def parse_args():
    """
    Parse the command line.  Required commands is the name of the "org/repo"
    Will accept many repos on the command line, and they can be in different orgs
    Also can take the output in a file.  one "org/repo" per line.
    Detects if no PAT is given, asks for it.
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(
        description="Gets a latest activity for a repo or list of repos"
    )
    parser.add_argument(
        "repos",
        help="list of repos to examine - or use --file for file base input",
        action="store",
        nargs="*",
    )
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    parser.add_argument("--file", help="File of 'owner/repo' names, 1 per line", action="store")
    parser.add_argument(
        "--parse-commit",
        help="look at the weekly commits of the repo."
        "  Only useful if you care about usage in the last year.",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        action="store_true",
        default=False,
        dest="info",
        help="Give visual output of that progress continues - "
        "useful for long runs redirected to a file",
    )
    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def repo_activity(gh_sess, org, repo):  # pylint: disable=too-many-branches
    """
    Look at the repo, and return activity, with the date of their latest commit,
        or no commit, over the last year
    :param gh_sess: an initialized github session
    :param org: the organization (or owner) name
    :param repo: the repo name
    :return: Status code of the commits iterator for retry purposes.
    """
    short_repo = gh_sess.repository(org, repo)

    commitlist = {}
    repo = short_repo.refresh()
    topdate = 0
    status_code = 200
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
            if week["total"] != 0:
                if week["week"] > topdate:
                    topdate = week["week"]
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
    if commitval == 0 and topdate == 0:
        # no commits found, update list as apropos
        commitval = "None"
    elif topdate != 0:
        commitval = datetime.fromtimestamp(topdate)
    commitlist[repo.name] = {
        "created_at": repo.created_at,
        "updated_at": repo.pushed_at,
        "admin_update": repo.updated_at,
        "last_commit": commitval,
        "private": repo.private,
        "archived": repo.archived,
    }

    for repo in commitlist:
        print(
            f"{repo},{commitlist[repo]['created_at']},"
            f"{commitlist[repo]['updated_at']},"
            f"{commitlist[repo]['admin_update']},"
            f"{commitlist[repo]['last_commit']},"
            f"{commitlist[repo]['private']},"
            f"{commitlist[repo]['archived']}"
        )
    return status_code


def mini_repo_activity(gh_sess, org, repo):
    """
    Print out only the top level repo data without looking at the last years commits.
    :param gh_sess: an initialized GH session
    :param org: string of the org
    :param repo: string of the repo
    :result: Prints out the data.
    """
    short_repo = gh_sess.repository(org, repo)
    repo = short_repo.refresh()
    print(
        f"{repo.name},{repo.created_at},{repo.pushed_at},{repo.updated_at},unexamined,{repo.private},{repo.archived}"
    )


def main():
    """
    Given a list of repos, and an org, get some data around last use
    """

    args = parse_args()

    repolist = []
    if args.repos != []:
        repolist = args.repos
    else:
        # Rip open the file, make a list
        txtfile = open(args.file, "r")
        repolist = txtfile.readlines()
        txtfile.close()

    gh_sess = login(token=args.token)

    # Print out the header.
    print("Repo, Created, Updated, Admin_update, Last_commit, Private, Archive_status")

    for orgrepo in repolist:
        org = orgrepo.split("/")[0].strip()
        repo = orgrepo.split("/")[1].strip()
        done = False
        count = 0
        if args.parse_commit:
            while not done:
                # Note: we add up to 5 lines
                #       to the file for a 202-failed point.
                #       Given the structure, it's unclear how to fix, and it's rare
                count += 1
                result = repo_activity(gh_sess, org, repo)
                if result != 202 or count >= MAX_RETRIES:
                    # print(f'Leaving Loop - result: {result}, '
                    #       f'done: {done}, count: {count}, repo: {repo}', file = sys.stderr)
                    if count == MAX_RETRIES and result == 202:
                        # We errored out --- put in something in the output to that effect.
                        print(
                            f"{org}/{repo},GH Gave 202 Error "
                            f"- failed out after {MAX_RETRIES} attempts.",
                            file=sys.stderr,
                        )
                    done = True
                utils.check_rate_remain(gh_sess, RATE_PER_LOOP, args.info)

                if result == 202:
                    sleep(10)
                if args.info:
                    utils.spinner()
        else:
            mini_repo_activity(gh_sess, org, repo)
            if args.info:
                utils.spinner()

    if args.info:
        print(file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script for determining activity levels of a repo
report the updated at (that's the last commit), created, and admin updates
Also look to see if there's a wiki, and check for activity there.
Used to help determination for archiving/moving repos that aren't active
"""

import sys
import tempfile
from datetime import datetime

import pytz
from git import Repo
from git import exc as git_exceptions
from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils

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

    parser = utils.GH_ArgParser(
        description="Gets a latest activity for a repo or list of repos.  "
        "Also checks wiki for activity, and can be told to check for issues activity."
    )
    parser.add_argument(
        "repos",
        help="list of repos to examine - or use --file for file base input",
        action="store",
        nargs="*",
    )
    parser.add_argument(
        "--issues",
        help="Check the issues to set a date of activity if more recent than code",
        action="store_true",
    )
    parser.add_argument("--file", help="File of 'owner/repo' names, 1 per line", action="store")
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
    return args


# def repo_activity(gh_sess, org, repo):  # pylint: disable=too-many-branches
#     """
#     Look at the repo, and return activity, with the date of their latest commit,
#         or no commit, over the last year
#     :param gh_sess: an initialized github session
#     :param org: the organization (or owner) name
#     :param repo: the repo name
#     :return: Status code of the commits iterator for retry purposes.
#     """
#     short_repo = gh_sess.repository(org, repo)

#     commitlist = {}
#     repo = short_repo.refresh()
#     topdate = 0
#     status_code = 200
#     commits = repo.commit_activity()
#     # Look through the last year of commit activity
#     # for each week, see if there's any commits
#     # if there is, and it's a more recent week than we have recorded, record it.
#     # (some returns from the commit_activity are out of order, hence
#     # we can't just look at the last active week and assume it's the most recent)

#     # Note: Repos with LOTS of activity (gecko-dev for one) are SO busy that commit
#     # stats for them will ALWAYS return a 202.  This is basically expected.
#     status_code = commits.last_status
#     try:
#         first = True
#         for week in commits:
#             # print(f'Result: {commits.last_status}, repo: {repo.name}', file = sys.stderr)
#             if first:
#                 status_code = commits.last_status
#                 # print(f'Result: {commits.last_status}, response: '
#                 #       f'{commits.last_response}, repo: {repo.name}', file = sys.stderr)
#                 if status_code == 202:
#                     return status_code
#                 first = False
#             if week["total"] != 0:
#                 if week["week"] > topdate:
#                     topdate = week["week"]
#         commitval = 0
#     except gh_exceptions.UnexpectedResponse:
#         # print(f'UNEXPECTED: Result: {commits.last_status}, response: '
#         #       f'{commits.last_response}, repo: {repo.name}', file = sys.stderr)
#         commitval = "Unexpected, possibly empty repo"
#     except gh_exceptions.NotFoundError:
#         # print(f'NOTFOUND: Result: {commits.last_status}, response: '
#         #       f'{commits.last_response}, repo: {repo.name}', file = sys.stderr)
#         commitval = "Unexpected, possibly temp repo"
#     finally:
#         status_code = commits.last_status
#     if commitval == 0 and topdate == 0:
#         # no commits found, update list as apropos
#         commitval = "None"
#     elif topdate != 0:
#         commitval = datetime.fromtimestamp(topdate)
#     commitlist[repo.name] = {
#         "created_at": repo.created_at,
#         "updated_at": repo.pushed_at,
#         "admin_update": repo.updated_at,
#         "last_commit": commitval,
#         "private": repo.private,
#         "archived": repo.archived,
#     }

#     for repo in commitlist:
#         print(
#             f"{repo},{commitlist[repo]['created_at']},"
#             f"{commitlist[repo]['updated_at']},"
#             f"{commitlist[repo]['admin_update']},"
#             f"{commitlist[repo]['last_commit']},"
#             f"{commitlist[repo]['private']},"
#             f"{commitlist[repo]['archived']}"
#         )
#     return status_code


def get_wiki_date(reponame, token):
    """
    Get the date of the last activity on the wiki - if there is one.
    :param reponame: name of the org/repo to examine
    Note that this assumes there is a wiki, so test before calling here.
    :result: datetime of the last commit to the wiki
    """
    # Setup the URL/paths
    remoteURL = f"https://{token}:x-oauth-basic@github.com/{reponame}.wiki.git"
    localpath = tempfile.TemporaryDirectory()
    try:
        # Checkout the repo
        clone = Repo.clone_from(remoteURL, localpath, depth="1")
        lastcommit = clone.commit("HEAD")
        date = datetime.fromtimestamp(lastcommit.committed_date, tz=pytz.UTC)
        clone.close()
    except git_exceptions.GitCommandError:
        # print(f"Tried finding a wiki on a non-wiki repo, likely uninitialized.  Repo: {reponame}", file=sys.stderr)
        date = datetime(year=1900, month=1, day=1, tzinfo=pytz.UTC)
    finally:
        localpath.cleanup()
    return date


def mini_repo_activity(gh_sess, orgstr, repostr, token, issues, info):
    """
    Print out only the top level repo data without looking at the last years commits.
    :param gh_sess: an initialized GH session
    :param orgstr: string of the org
    :param repostr: string of the repo
    :param token: PAT needed for wiki analysis
    :param issues: booolean about whether to look at issues
    :param info: Should I output spinners, etc?
    :result: Prints out the data.
    """
    utils.check_rate_remain(gh_sess)
    try:
        short_repo = gh_sess.repository(orgstr, repostr)
        repo = short_repo.refresh()
        # This gets us the commit date (pushed_at) but ignores the wiki
        pushed_date = repo.pushed_at
        if repo.has_wiki:
            # print(f"Found a Wiki: {repo.full_name}", file=sys.stderr)
            wikidate = get_wiki_date(repo.full_name, token)
            if wikidate > pushed_date:
                pushed_date = wikidate

        issue_whacky = ""
        if issues:
            issuecount = repo.open_issues_count
            # If you have >1K issues open - SOMETHING's happening - set the activity to today
            if issuecount > 1000:
                pushed_date = datetime.now()
                issue_whacky = "-MANY-ISSUES"
            else:
                issuelist = repo.issues(state="open")
                for issue in issuelist:
                    utils.check_rate_remain(gh_sess, update=info)
                    if info:
                        utils.spinner()
                    issuedate = issue.updated_at
                    if issuedate > pushed_date:
                        pushed_date = issuedate

        if issues:
            print(
                f"{orgstr}/{repo.name}{issue_whacky},{repo.created_at.strftime('%Y-%m-%d')},"
                f"{pushed_date.strftime('%Y-%m-%d')},{repo.updated_at.strftime('%Y-%m-%d')},"
                f"{repo.private},{repo.archived},{issuecount}"
            )
        else:
            print(
                f"{orgstr}/{repo.name}{issue_whacky},{repo.created_at.strftime('%Y-%m-%d')},"
                f"{pushed_date.strftime('%Y-%m-%d')},{repo.updated_at.strftime('%Y-%m-%d')},"
                f"{repo.private},{repo.archived}"
            )
    except gh_exceptions.ConnectionError:
        print(f"Timeout error, 'CLOUD' on repo {orgstr}/{repostr}", file=sys.stderr)


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
    if args.issues:
        print("Org/Repo, Created, Updated, Admin_update, Private, Archive_status, Issue_Count")
    else:
        print("Org/Repo, Created, Updated, Admin_update, Private, Archive_status")

    for orgrepo in repolist:
        org = orgrepo.split("/")[0].strip()
        repo = orgrepo.split("/")[1].strip()
        # ignore ghsa repos --- they only lead to heartache when automated things interact
        if repo.find("-ghsa-") == -1:
            mini_repo_activity(gh_sess, org, repo, args.token, issues=args.issues, info=args.info)
        if args.info:
            utils.spinner()

    if args.info:
        print(file=sys.stderr)


if __name__ == "__main__":
    main()

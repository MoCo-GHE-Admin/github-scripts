#!/usr/bin/env python
"""
Script for determining activity levels of a repo
report the updated at (that's the last commit), created, and admin updates
Also look to see if there's a wiki, and check for activity there.
Used to help determination for archiving/moving repos that aren't active
"""

import sys
import tempfile
from datetime import date, datetime

import alive_progress
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
        "--org",
        help="Look at all the repos in the org, will ignore archived repos by default",
        action="store",
    )
    parser.add_argument(
        "--date",
        help="YYYYMMDD, ignore anything with update date after this date.",
        action="store",
        type=date.fromisoformat,
    )
    parser.add_argument(
        "--issues",
        help="Check the issues to set a date of activity if more recent than code",
        action="store_true",
    )
    parser.add_argument(
        "--ignore-wiki", dest="ignore_wiki", action="store_true", help="Don't do the wiki analysis"
    )
    parser.add_argument(
        "--archived",
        help="if doing org level, should we include archived repos?",
        action="store_true",
    )
    parser.add_argument("--file", help="File of 'owner/repo' names, 1 per line", action="store")
    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    return args


def get_wiki_date(reponame, token):
    """
    Get the date of the last activity on the wiki - if there is one.
    :param reponame: name of the org/repo to examine
    Note that this assumes there is a wiki, so test before calling here.
    :result: datetime of the last commit to the wiki
    """
    # Setup the URL/paths
    remoteURL = f"https://{token}:x-oauth-basic@github.com/{reponame}.wiki.git"  # noqa: E231
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


def mini_repo_activity(gh_sess, orgstr, repostr, token, issues, ignore_wiki, filterdate, bar):
    """
    Print out only the top level repo data without looking at the last years commits.
    :param gh_sess: an initialized GH session
    :param orgstr: string of the org
    :param repostr: string of the repo
    :param token: PAT needed for wiki analysis
    :param issues: booolean about whether to look at issues
    :param ignore_wiki: boolean - should we ignore the wiki
    :param filterdate: date - If pushed is > filter_date, ignore this repo
    :param bar: the progress bar
    :result: returns a list of strings of the results
    """
    utils.check_rate_remain(gh_sess)
    try:
        short_repo = gh_sess.repository(orgstr, repostr)
        repo = short_repo.refresh()
        # This gets us the commit date (pushed_at) but ignores the wiki
        pushed_date = repo.pushed_at
        if repo.has_wiki and not ignore_wiki:
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
                    utils.check_rate_remain(gh_sess)
                    bar()
                    issuedate = issue.updated_at
                    if issuedate > pushed_date:
                        pushed_date = issuedate

        # Break out if we're on a repo that doesn't meet the date.
        if filterdate is not None and filterdate < datetime.date(pushed_date):
            result_string = None
        else:
            if issues:
                result_string = (
                    f"{orgstr}/{repo.name}{issue_whacky},{repo.created_at.strftime('%Y-%m-%d')},"  # noqa: E231
                    f"{pushed_date.strftime('%Y-%m-%d')},{repo.updated_at.strftime('%Y-%m-%d')},"  # noqa: E231
                    f"{repo.private},{repo.archived},{repo.fork},{issuecount}"  # noqa: E231
                )
            else:
                result_string = (
                    f"{orgstr}/{repo.name}{issue_whacky},{repo.created_at.strftime('%Y-%m-%d')},"  # noqa: E231
                    f"{pushed_date.strftime('%Y-%m-%d')},{repo.updated_at.strftime('%Y-%m-%d')},"  # noqa: E231
                    f"{repo.private},{repo.archived},{repo.fork}"  # noqa: E231
                )
    except gh_exceptions.ConnectionError:
        print(f"Timeout error, 'CLOUD' on repo {orgstr}/{repostr}", file=sys.stderr)
    return result_string


def main():
    """
    Given a list of repos, and an org, get some data around last use
    """

    args = parse_args()

    gh_sess = login(token=args.token)

    repolist = []
    if args.repos != []:
        repolist = args.repos
    elif args.org is not None:
        for repo in gh_sess.organization(args.org).repositories():
            if args.archived or not repo.archived:
                repolist.append(repo.full_name)
    else:
        # Rip open the file, make a list
        txtfile = open(args.file, "r")
        repolist = txtfile.readlines()
        txtfile.close()

    output_str = []
    # Print out the header.
    if args.issues:
        output_str.append(
            "Org/Repo,Created,Updated,Admin_update,Private,Archive_status,IsFork,Issue_Count"
        )
    else:
        output_str.append("Org/Repo,Created,Updated,Admin_update,Private,Archive_status,IsFork")

    with alive_progress.alive_bar(
        dual_line=True,
        title="Getting activity",
        file=sys.stderr,
        length=20,
        force_tty=True,
        disable=False,
    ) as bar:
        for orgrepo in repolist:
            org = orgrepo.split("/")[0].strip()
            repo = orgrepo.split("/")[1].strip()
            # ignore ghsa repos --- they only lead to heartache when automated things interact
            if repo.find("-ghsa-") == -1:
                repostr = mini_repo_activity(
                    gh_sess,
                    org,
                    repo,
                    args.token,
                    issues=args.issues,
                    ignore_wiki=args.ignore_wiki,
                    filterdate=args.date,
                    bar=bar,
                )
                if repostr is not None:
                    output_str.append(repostr)
            bar()
    print("\n".join(output_str))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script to determine the activity of users in a repo
Given a list of repos, and a timefame, check out the repo
and return the list of unique users in that repo
"""

import sys
import tempfile

import alive_progress
import github3
from git import Repo

from github_scripts import utils


def parse_args():
    """
    Parse the command line.
    Need either repo and org - or if no repo supplied, org.
    Timeframe to look over.  Default to 30 days.
    """

    parser = utils.GH_ArgParser(
        description="Gets a list of active users for a list of repos"
        "Also checks wiki for activity, and can be told to check for issues activity."
    )
    parser.add_argument(
        "org",
        help="The organization that the repos belong to",
    )
    parser.add_argument(
        "--days", help="How many days back to look, default, 30", type=int, default=30
    )
    parser.add_argument(
        "repos",
        help="list of repos to examine - or use --file for file base input",
        action="store",
        nargs="+",
    )
    parser.add_argument(
        "--author",
        help="Use the author rather than committer email, if you're concerned about people with permissions, committer is what you want",
        action="store_true",
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    userset = set()
    # Are we looking at author emails, or committer?
    if args.author:
        format = "%ae"
    else:
        format = "%ce"
    gh_sess = github3.login(token=args.token)
    with alive_progress.alive_bar(
        dual_line=True,
        title="Getting Perms",
        file=sys.stderr,
        length=20,
        force_tty=True,
        disable=False,
    ) as bar:
        for repo in args.repos:
            bar.text(f"working on repo: {repo}")
            url = f"https://{args.token}:x-oauth-basic@github.com/{args.org}/{repo}.git"
            localpath = tempfile.TemporaryDirectory()
            workingset = set()
            try:
                clone = Repo.clone_from(url, localpath)
                emailstr = clone.git.log(since=f"{args.days} days ago", pretty=f"tformat:{format}")
                if emailstr != "":
                    emaillist = emailstr.split("\n")
                    workingset = set(emaillist)
                if args.debug:
                    print(f"\t\tEmailSTR: {emailstr}", file=sys.stderr)
            finally:
                localpath.cleanup()
            utils.check_rate_remain(gh_sess, bar=bar)
            userset |= workingset
    print(f"Unique author emails found in the org {args.org} org and the repos you asked about:")
    for item in userset:
        print(item)


if __name__ == "__main__":
    main()

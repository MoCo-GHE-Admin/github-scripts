#!/usr/bin/env python
"""
Script for unarchiving repo
Assumes that the repo was archived with the repo_archiver script
Takes an Owner/repo and does the following
reverts topic changes
uses the ARCHIVED label to reopen issues/PRs
Reverts description changes
un-archives the repo

Unlike the archiver - this works with 1 repo only.
assumption being that unarchiving is rarer than archiving.
"""

import argparse
import sys
from getpass import getpass

from github3 import exceptions as gh_exceptions
from github3 import login


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = argparse.ArgumentParser(
        description="Reverse archival closing of issues of the specified repo, Note, repo "
        "MUST be manually unarchived before this script"
    )
    parser.add_argument("repo", help="owner/repo to unarchive", action="store")
    parser.add_argument(
        "--token",
        help="PAT to access github.  Needs Write access to the repos",
        action="store",
    )
    parser.add_argument(
        "-q",
        help="DO NOT print, or request confirmations",
        dest="quiet",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def main():
    """
    Main logic for the archiver
    """
    args = parse_args()
    gh_sess = login(token=args.token)
    try:
        org = args.repo.split("/")[0].strip()
        repo = args.repo.split("/")[1].strip()
    except IndexError:
        print(f"{args.repo} needs to be in the form ORG/REPO")
        sys.exit()

    try:
        gh_repo = gh_sess.repository(owner=org, repository=repo)
    except gh_exceptions.NotFoundError:
        print(f"Trying to open {org=}, {repo=}, failed with 404")
        sys.exit()

    if not args.quiet:
        print(f"Working with repo: {gh_repo.name}")
        print("\tRe-opening issues/PRs")
    issues = gh_repo.issues(state="closed", labels="ARCHIVED")
    for issue in issues:
        issue.edit(state="open")
        if not args.quiet:
            print(f"\tReopening issue/PR {issue.title}")
    for issue in issues:
        issue.remove_label("ARCHIVED")
    gh_repo.label("ARCHIVED").delete()
    topics = gh_repo.topics().names
    topics.remove("unmaintained")
    topics.remove("abandoned")
    if not args.quiet:
        print("\tFixing topics")
    gh_repo.replace_topics(topics)

    new_desc = gh_repo.description.replace("DEPRECATED - ", "").replace(
        "DEPRECATED", ""
    )
    if not args.quiet:
        print(f"\tFixing description, completed revert of repo {repo}")
    gh_repo.edit(name=gh_repo.name, description=new_desc)


if __name__ == "__main__":
    main()

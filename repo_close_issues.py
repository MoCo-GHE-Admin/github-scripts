#!/usr/bin/env python
"""
Script for closing issues
PR's are "special" issues - flag for including those if desired.
defaults to Dry run - will print out everything that will happen without DOING anything.
"""

import argparse
import time
from getpass import getpass

from github3 import exceptions as gh_exceptions
from github3 import login

import utils


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = argparse.ArgumentParser(
        description="Close issues associated with the specified repo.  Do not close PRs unless specified, and only do things if specified"
    )
    parser.add_argument("org", help="Org/owner name")
    parser.add_argument("repo", help="Name of the repo")
    parser.add_argument(
        "--close-pr", help="Close the PRs too?", dest="close_pr", action="store_true"
    )
    parser.add_argument("--comment", help="A comment to close the issue with")
    parser.add_argument("--doit", help="Actually close things", action="store_true")
    parser.add_argument(
        "--token", help="PAT to access github.  Needs Write access to the repos", action="store"
    )
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    args = parser.parse_args()
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def close_issue(issue, comment):
    """
    Close the issue, with error handling
    issue: the issue object in question
    comment: A comment to close with, or None
    """
    try:
        if comment is not None:
            issue.create_comment(comment)
        issue.close()
    except gh_exceptions.UnprocessableEntity:
        print(
            f"Got 422 Unproccessable on issue {issue.title},"
            " continuing.  May need to run again, or manually finish closing."
        )


def main():
    """
    Parse the CLI, log in, get the repo, and process the issues as specified.
    """
    args = parse_args()
    gh_sess = login(token=args.token)

    repo = gh_sess.repository(owner=args.org, repository=args.repo)
    print(f"Working on repository {args.org}/{args.repo}")

    issues = repo.issues(state="open")
    for issue in issues:
        utils.check_rate_remain(gh_sess)
        if issue.pull_request_urls is not None:
            is_PR = True
        else:
            is_PR = False
        if is_PR and args.close_pr:
            if args.doit:
                print(f'PR found: "{issue.title}", closing.', end="")
                close_issue(issue, args.comment)
                print(" Closed.")
            else:
                print(f'PR found "{issue.title}", not closing due to dry run')
        if not is_PR:
            if args.doit:
                print(f'Issue found: "{issue.title}", closing.', end="")
                close_issue(issue, args.comment)
                print(" Closed.")
                # Secondary Rate limit avoidance
                #
                time.sleep(1.1)
            else:
                print(f'Issue found "{issue.title}", not closing due to dry run')


if __name__ == "__main__":
    main()

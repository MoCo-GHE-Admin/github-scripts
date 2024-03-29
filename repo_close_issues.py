#!/usr/bin/env python
"""
Script for closing issues
PR's are "special" issues - flag for including those if desired.
defaults to Dry run - will print out everything that will happen without DOING anything.
"""

import time

from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = utils.GH_ArgParser(
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
        "--delay",
        default=2,
        type=float,
        help="seconds between close requests, to avoid secondary rate limits > 1",
    )
    args = parser.parse_args()
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
                # https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-secondary-rate-limits
                time.sleep(args.delay)
            else:
                print(f'Issue found "{issue.title}", not closing due to dry run')


if __name__ == "__main__":
    main()

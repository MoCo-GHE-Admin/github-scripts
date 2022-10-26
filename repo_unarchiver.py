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

Per GitHub API docs, MUST manually unarchive:
https://docs.github.com/en/rest/reference/repos#update-a-repository
Note: You cannot unarchive repositories through the API.
"""

import argparse
import sys
from getpass import getpass

from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils

# TODO: CUSTOM LABEL TEXT REMEDIATION


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
        "--token", help="PAT to access github.  Needs Write access to the repos", action="store"
    )
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use, default: 'admin'",
    )
    parser.add_argument(
        "-q",
        help="DO NOT print, or request confirmations",
        dest="quiet",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def handle_issues(repo, quiet):
    """
    Find any custom label, and reopen and unlabel issues.
    Return the label name that was found.  (Assumption - "ARCHIVED" is the seed)
    :param repo: initialized gh repo object
    :param quiet: if true, we won't print out things.
    return: labelname that was found.
    """
    do_the_label_remove = True
    if not quiet:
        print("\tFinding if there's a custom label")

    labelname = "ARCHIVED"
    labellist = repo.labels()
    for label in labellist:
        if label.name.find("ARCHIVED") != -1:
            labelname = label.name

    if not quiet:
        print(f"\tFound labelname: {labelname}")

    issues = repo.issues(state="closed", labels=labelname)

    for issue in issues:
        try:
            issue.edit(state="open")
            if not quiet:
                print(f"\tReopening issue/PR {issue.title}")
        except gh_exceptions.UnprocessableEntity:
            # Hit an un-reopenable issue
            do_the_label_remove = False
            if not quiet:
                print(f"\t\tUnable to reopen issue {issue.title}")
    if do_the_label_remove:
        for issue in issues:
            issue.remove_label(labelname)
        try:
            repo.label(labelname).delete()
        except gh_exceptions.NotFoundError:
            print(
                "No ARCHIVED label found, was this archived?  manually remove topics and update description..."
            )
            sys.exit()
    return labelname


def handle_topics(repo, quiet):
    """
    Remove the unmaintained, abandoned, inactive topics if they're there.
    :param repo: is the initialized repo object
    :param quiet: should we not print out?
    """
    topics = repo.topics().names
    if "unmaintained" in topics:
        topics.remove("unmaintained")
    if "abandoned" in topics:
        topics.remove("abandoned")
    if "inactive" in topics:
        topics.remove("inactive")
    if not quiet:
        print("\tFixing topics")
    repo.replace_topics(topics)


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

    if gh_repo.archived:
        print(
            "This repo is still archived, per "
            "https://docs.github.com/en/rest/reference/repos#update-a-repository "
            "you must manually unarchive, then this script can clean up the other changes."
        )
        sys.exit()

    if not args.quiet:
        print(f"Working with repo: {gh_repo.name}")
        print("\tRe-opening issues/PRs")
    # TODO: find custom label

    labelname = handle_issues(repo=gh_repo, quiet=args.quiet)

    handle_topics(repo=gh_repo, quiet=args.quiet)

    customstr = labelname.replace("ARCHIVED - ", "")
    if gh_repo.description is not None:
        # Remove the DEPRECATED if it exists.
        new_desc = gh_repo.description.replace("DEPRECATED - ", "", 1).replace("DEPRECATED", "", 1)
        # Remove the INACTIVE if it exists.
        new_desc = new_desc.replace("INACTIVE - ", "", 1).replace("INACTIVE", "", 1)
        # Remove the custom label if it exists.
        new_desc = new_desc.replace(customstr + " - ", "", 1).replace(customstr, "", 1)

        if not args.quiet:
            print(f"\tFixing description, completed revert of repo {repo}")
        gh_repo.edit(name=gh_repo.name, description=new_desc)


if __name__ == "__main__":
    main()

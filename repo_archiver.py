#!/usr/bin/env python
"""
Script for archiving repo
Takes an Owner/repo and does the following
Creates a label "ARCHIVED" in red (or specified)
Applies that label to all open issues and PR's
prepends "DEPRECATED - " to the description
Archives the repo
"""

import argparse
import sys
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
        description="Archive the specified repo, closing out issues and PRs"
    )
    parser.add_argument("repos", help="owner/repo to archive", nargs="*", action="store")
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
    parser.add_argument(
        "--file", help='File with "owner/repo" one per line to archive', action="store"
    )
    parser.add_argument(
        "--force", help="Don't stop if you detect previous archivers", action="store_true"
    )
    parser.add_argument(
        "-q",
        help="DO NOT print, or request confirmations",
        dest="quiet",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def handle_issues(repo, force=False, quiet=False):
    """
    Handle labelling the issues and closing them out reversibly
    :param repo: the initialized repo object
    :param force: if we run into a label conflict, do we barrel through?
    :param quiet: should we talk out loud?
    :return: True is all is well, False if there was an exception that we handled
    """

    result = True

    if not quiet:
        print("\tcreating archive label")

    labellist = repo.labels()

    need_flag = True
    for label in labellist:
        if label.name == "ARCHIVED":
            need_flag = False
            if not force:
                print(
                    "Uh oh.  ARCHIVED label already exists?  Closing out so I don"
                    "t "
                    "step on other processes"
                )
                sys.exit()
    if need_flag:
        repo.create_label(
            name="ARCHIVED", color="#c41a1a", description="CLOSED at time of archiving"
        )
    if not quiet:
        print("\tStarting work on issues")
    issues = repo.issues(state="open")
    # Need to do two passes - if we do one pass, the closure erases the label
    for issue in issues:
        # update label
        issue.add_labels("ARCHIVED")
    for issue in issues:
        try:
            issue.close()
            if not quiet:
                print(f"\tLabeled and closed issue: {issue.title}")
        except gh_exceptions.UnprocessableEntity:
            result = False
            print(
                f"Got 422 Unproccessable on issue {issue.title},"
                " continuing.  May need to run --force or manually finish closing."
            )
    return result


def main():
    """
    Main logic for the archiver
    """
    args = parse_args()
    gh_sess = login(token=args.token)

    repolist = []
    if args.repos != []:
        repolist = args.repos
    elif args.file:
        try:
            # Rip open the file, make a list
            txtfile = open(args.file, "r")
            repolist = txtfile.readlines()
            txtfile.close()
        except Exception:
            print("Problem loading file!")
            return
    else:
        print("Please specify an org/repo or a file.")
        return

    for orgrepo in repolist:
        try:
            org = orgrepo.split("/")[0].strip()
            repo = orgrepo.split("/")[1].strip()
        except IndexError:
            print(f"{orgrepo} needs to be in the form ORG/REPO")
            sys.exit()
        try:
            gh_repo = gh_sess.repository(owner=org, repository=repo)
        except gh_exceptions.NotFoundError:
            print(f"Trying to open {org=}, {repo=}, failed with 404")
            sys.exit()

        if gh_repo.archived:
            if not args.quiet:
                print(f"repo {gh_repo.name} is already archived, skipping")
        else:

            if not args.quiet:
                print(f"working with repo: {gh_repo.name}")

            # Deal with issues

            handled = handle_issues(gh_repo, args.force, args.quiet)

            # Handle the overall repo marking:

            topics = gh_repo.topics().names
            topics.append("abandoned")
            topics.append("unmaintained")
            gh_repo.replace_topics(topics)
            if not args.quiet:
                print("\tUpdated topics")
            description = gh_repo.description
            if description is not None:
                description = "DEPRECATED - " + description
            else:
                description = "DEPRECATED"
            if handled:
                gh_repo.edit(name=gh_repo.name, description=description, archived=True)
                if not args.quiet:
                    print(f"\tUpdated description and archived the repo {repo}")
            else:
                gh_repo.edit(name=gh_repo.name, description=description)
                print(
                    f"\tUpdated description, but there was a problem with issues in repo {repo}"
                    ", pausing so you can fix and manually archive"
                )
                getpass("Press enter to continue")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script to create/update issues
can either use command line, or a yaml file for issue options
If the issue exists, can reopen it, and will add a comment to it
Else, will file a new issue per the configuration
"""

import os
import sys
from logging import exception

import yaml
from github3 import exceptions as gh_exceptions
from github3 import login

import github_scripts.utils


def parse_arguments():
    """
    Parse the CLI for the needed arguments
    """
    parser = github_scripts.utils.GH_ArgParser(
        description="Given a list of org/repos, open an issue in each based on the settings in the conf yaml file.  If update is specified, will reopen closed issues, and add a comment to any found issues of the same bodyUID field"
    )
    parser.add_argument(
        "repos",
        type=str,
        help="The repos to work on as org/repo space delimited",
        action="store",
        nargs="+",
    )
    parser.add_argument(
        "--conf", type=str, help="The yaml file to use - see issueconf.yaml.example", required=True
    )
    parser.add_argument(
        "--reopen",
        action="store_true",
        help="Should we reopen closed issues?",
    )
    parser.add_argument(
        "--always-comment",
        help="Always add the comment, even if it already exists.",
        action="store_true",
        dest="always_comment",
    )

    args = parser.parse_args()
    # Process the conf file
    if args.conf is not None:
        home = os.path.expanduser("~")
        config_file_name = args.conf
        if os.path.exists(config_file_name):
            config_file = config_file_name
        elif os.path.exists(os.path.join(home, config_file_name)):
            config_file = os.path.join(home, config_file_name)
        else:
            raise exception(f"File {args.conf} not found")
        try:
            with open(config_file, "r") as file:
                config = yaml.safe_load(file)
            args.title = config["title"]
            args.body = config["body"]
            args.body_uid = config["bodyUID"]
            args.comment = config["comment"]

        # TODO: get value from dict, but have it use a default if needed?

        except Exception:
            print("Error processing config file, or command line")
            sys.exit()

    return args


def find_issue(gh_sess, orgrepo, uid):
    """
    given an initialized gh_sess object, an org/repo, and a unique text string in the issue body, look for an issue matching and return it, or None.
    param gh_sess: the initialized github session
    param orgrepo: string of the "org/repo" to look in
    param uid: the string in the body of the issue to match.
    return: None if nothing found, or the issue object.
    """
    issuequery = f"{uid} type:issue repo:{orgrepo}"
    search_results = list(gh_sess.search_issues(query=issuequery))
    num_results = len(search_results)
    if num_results == 0:
        return None
    elif num_results > 0:
        return search_results[0].issue
    else:
        print("\t\tMORE THAN ONE ISSUE FOUND, Returning first one.")
        return search_results[0].issue


def comment_exists(issue, commentstr):
    """
    Given a commentstr - look for that as a comment in the issue - if it's there, return True, else False
    Used to make sure we don't recomment
    param issue: the initialized issue that we're looking for comments in
    param commenstr: the contents of the comment
    return: True if found, False if not
    """
    result = False
    for comment in issue.comments():
        if comment.body == commentstr:
            result = True
    return result


def handle_existing_issue(issue, comment, reopen, always_comment):
    """
    if we found an existing issue - handle it - either commenting, or reopening and commenting
    Note, if this is run again, it will add another comment of the same to this issue.
    param issue: the initialized issue object
    param comment: the comment to add
    param reopen: boolean of whether to reopen closed objects
    param always_comment: boolean of whether to add the comment no matter what if the issue is open
    """
    if issue.state == "closed":
        closed = True
    else:
        closed = False
    existing_comment = comment_exists(issue, comment)

    if closed:
        if reopen:
            issue.edit(state="open")
            if not existing_comment or always_comment:
                if comment is not None:
                    issue.create_comment(comment)
                    print("\t\tIssue was closed, reopened, comment added")
                else:
                    print("\t\tIssue was closed, reopened, no comment specified")
            else:
                print("\t\tIssue reopened, comment already existed")
        else:
            print("\t\tIssue was closed, and no reopen flag")
    else:
        if not existing_comment or always_comment:
            if comment is not None:
                issue.create_comment(comment)
                print("\t\tadding comment")
            else:
                print("\t\tNo comment specified")
        else:
            print("\t\tcomment exists, or always-comment not set, NOT commenting")


def main():
    """
    from the list of repos, look for the issue and create, update, reopen as necessary
    """
    args = parse_arguments()
    gh_sess = login(token=args.token)
    for orgrepo in args.repos:
        github_scripts.utils.check_rate_remain(gh_sess=gh_sess)
        try:
            org = orgrepo.split("/")[0].strip()
            repo = orgrepo.split("/")[1].strip()
        except IndexError:
            print(f"{orgrepo} needs to be in the form ORG/REPO")
            sys.exit()
        try:
            gh_repo = gh_sess.repository(owner=org, repository=repo)
        except gh_exceptions.NotFoundError:
            print(f"Trying to open {org}/{repo}, failed with 404")
            sys.exit()
        print(f"Working with repo {org}/{repo}")
        print(f'\tSearching for issue titled "{args.title}"')
        found_issue = find_issue(gh_sess, orgrepo, args.body_uid)
        if found_issue is not None:
            print("\tFound issue, will comment if needed")
            handle_existing_issue(found_issue, args.comment, args.reopen, args.always_comment)
        else:
            print(f'\tCreating issue "{args.title}"')
            issue_body = args.body + "\n" + args.body_uid
            gh_repo.create_issue(title=args.title, body=issue_body)


if __name__ == "__main__":
    main()

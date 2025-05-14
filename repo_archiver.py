#!/usr/bin/env python
"""
Script for archiving repo
Takes an Owner/repo and does the following
Creates a label "ARCHIVED" in red (or specified)
Applies that label to all open issues and PR's
prepends "DEPRECATED - " to the description
Archives the repo
"""

import sys

import getch
from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils

# TODO: CUSTOM LABEL TEXT
MAX_CUSTOM_LENGTH = 50 - len("ARCHIVED - " + " - ")


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = utils.GH_ArgParser(
        description="Archive the specified repo, labelling and then closing out issues and PRs, "
        "per GitHub best practices.  Closed issues/PRs, and description/topic changes "
        "can be completely reversed using the repo_unarchiver script.  "
        "DEFAULTS to dry-run and will not modify things until --doit flag is applied.  "
        "Also, will report on any existing hooks or keys in the repos so that cleanup in related systems can occur"
    )
    parser.add_argument("repos", help="owner/repo to archive", nargs="*", action="store")
    parser.add_argument(
        "--inactive",
        help="Change the 'abandoned' and 'deprecated' wording to 'inactive'",
        action="store_true",
    )
    parser.add_argument(
        "--custom",
        help=f"Custom text to add to issue/PR label, and description, less than {MAX_CUSTOM_LENGTH} char long",
        type=str,
        action="store",
    )
    parser.add_argument(
        "--file", help='File with "owner/repo" one per line to archive', action="store"
    )
    parser.add_argument(
        "--disable-report",
        help="Disable the hook/keys report at the end of the process.",
        action="store_false",
        dest="show_report",
    )
    parser.add_argument(
        "--ignore-issue-label",
        help="Ignore the existence of the ARCHIVED issue label",
        action="store_true",
        dest="ignore_issue_label",
    )
    parser.add_argument(
        "--pause",
        help="Pause upon detecting anomalies that might need fixing, but aren't blockers",
        action="store_true",
    )
    parser.add_argument(
        "-q",
        help="DO NOT print, or request confirmations",
        dest="quiet",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--doit",
        help="Actually perform the archiving steps",
        action="store_true",
        dest="do_it",
    )
    args = parser.parse_args()
    if args.repos is None and args.file is None:
        raise Exception("Must have either a list of repos, OR a file to read repos from")
    if args.custom is not None and len(args.custom) > MAX_CUSTOM_LENGTH:
        raise Exception(f"Custom string must be less than {MAX_CUSTOM_LENGTH} characters")

    return args


def handle_issues(repo, custom, ignore_label=False, do_it=False, quiet=False):
    """
    Handle labelling the issues and closing them out reversibly
    :param repo: the initialized repo object
    :param custom: additional custom text for label
    :param ignore_label: if we run into a label conflict, do we barrel through?
    :param do_it: If true, we actually touch things.
    :param quiet: should we talk out loud?
    :return: True is all is well, False if there was an exception that we handled
    """

    result = True

    if not quiet:
        print("\tcreating archive label")

    labellist = repo.labels()

    if custom is None:
        labelname = "ARCHIVED"
    else:
        labelname = "ARCHIVED - " + custom

    print(f"\tLabelname is {labelname}")
    need_flag = True
    for label in labellist:
        if label.name.find(labelname) != -1:
            need_flag = False
            if not ignore_label:
                print(
                    "Uh oh.  ARCHIVED label already exists?  Closing out so I don"
                    "t "
                    "step on other processes"
                )
                sys.exit()
    if need_flag and do_it:
        repo.create_label(
            name=labelname, color="#c41a1a", description="CLOSED at time of archiving"
        )
    if not quiet:
        print(f"\tStarting work on {repo.open_issues_count} issues")
    issues = repo.issues(state="open")
    # Need to do two passes - if we do one pass, the closure erases the label
    for issue in issues:
        # update label
        if do_it:
            issue.add_labels(labelname)
    for issue in issues:
        try:
            if do_it:
                issue.close()
            if not quiet:
                print(f"\tLabeled and closed issue: {issue.title}")
        except gh_exceptions.UnprocessableEntity:
            result = False
            print(
                f"Got 422 Unproccessable on issue {issue.title},"
                " continuing.  May need to manually finish closing."
            )
    return result


def handle_topics(gh_repo, topic_inactive, do_it=False, quiet=False):
    """
    Given a repo, update the topics to indicate its inactivity - either the default ABANDONED language or INACTIVE if desired.
    :param gh_repo: the initialized repo object
    :param topic_inactive: boolean, should we use the milder language
    :param do_it: If true, we actually touch things.
    :param quiet: do we output anything?
    No return value
    """
    topics = gh_repo.topics().names
    if do_it:
        if topic_inactive:
            topics.append("inactive")
        else:
            topics.append("abandoned")
        topics.append("unmaintained")
        gh_repo.replace_topics(topics)
    if not quiet:
        print("\tUpdated topics")


def handle_hooks(gh_repo, ignore_hooks=False, disable_hooks=False):
    """
    Given an initialized repo, look for hooks.
    If hooks are found, disable them if asked to
    Return bool if there are any hooks still enabled, unless ignore is set
    :param gh_repo: initialized repo object
    :param ignore_hooks: just pretend everything is fine
    :param disable_hooks: disable existing hooks
    return: True if there are any hooks
    """
    # are there hooks
    hooklist = list(gh_repo.hooks())
    if len(hooklist) > 0:
        hooks_exist = True
    else:
        hooks_exist = False
    hooksdisabled = True
    if disable_hooks:
        for hook in hooklist:
            if not hook.edit(active=False):
                hooksdisabled = False  # Something went wrong trying to disable.
    if ignore_hooks:
        return False
    else:
        return hooks_exist and not hooksdisabled


def handle_keys(gh_repo, ignore_keys=False, delete_keys=False):
    """
    Given an initialized repo, look for keys.
    If keys are found, delete them if asked to
    Return bool if there are any keys existing, unless ignore is set
    :param gh_repo: initialized repo object
    :param ignore_keys: just pretend everything is fine
    :param delete_keys: delete existing keys
    return: True if there are any keys
    """
    keylist = list(gh_repo.keys())
    if len(keylist) > 0:
        keys_exist = True
    else:
        keys_exist = False
    if delete_keys:
        for key in keylist:
            key.delete()
    if ignore_keys:
        return False
    else:
        return keys_exist and not delete_keys


def report_on_hooks(repo):
    """
    Return a list of strings, "org,repo,hookURL,boolEnabled" for each hook found
    :param: the initialized repo object
    :result: a list of strings
    """
    result = []
    for hook in repo.hooks():
        result.append(f"HOOK,{repo.owner.login},{repo.name},{hook.config['url']},{hook.active}")
    return result


def report_on_keys(repo):
    """
    Return a list of strings, "org,repo,keyTitle,keycreated,keylastused" for each key found
    :param: the initialized repo object
    :result: a list of strings
    """
    result = []
    for key in repo.keys():
        result.append(
            f"KEY,{repo.owner.login},{repo.name},{key.title},{key.created_at},{key.last_used}"
        )
    return result


def main():
    """
    Main logic for the archiver
    """
    args = parse_args()
    gh_sess = login(token=args.token)
    key_report_list = ["type,org,repo,key"]
    hook_report_list = ["type,org,repo,hookURL,status"]

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
            print(f"Trying to open {org}/{repo}, failed with 404")
            sys.exit()

        if gh_repo.archived:
            if not args.quiet:
                print(f"repo {org}/{repo} is already archived, skipping")
        else:
            if not args.quiet:
                print(f"working with repo: {org}/{repo}")

            # If there are gh_pages - let people know about it.
            if gh_repo.has_pages:
                if args.pause:
                    print(
                        "\tNOTE: Repo has gh_pages - please deal with them in the UI and press any key to continue"
                    )
                    char = getch.getch()
                else:
                    print("\tNOTE: Repo has gh_pages")

            # Look for keys and hooks, and report on them at the end
            if args.show_report:
                key_report_list.extend(report_on_keys(gh_repo))
                hook_report_list.extend(report_on_hooks(gh_repo))

            # Deal with issues

            handled = handle_issues(
                gh_repo, args.custom, args.ignore_issue_label, args.do_it, args.quiet
            )
            # Handle the overall repo marking:

            handle_topics(gh_repo, args.inactive, args.do_it, args.quiet)

            description = gh_repo.description
            if args.inactive:
                preamble = "INACTIVE"
            else:
                preamble = "DEPRECATED"
            if args.custom is not None:
                preamble += " - " + args.custom
            if description is not None:
                description = preamble + " - " + description
            else:
                description = preamble

            if handled:
                if args.do_it:
                    gh_repo.edit(name=gh_repo.name, description=description, archived=True)
                    if not args.quiet:
                        print(f"\tUpdated description and archived the repo {org}/{repo}")
            elif True:
                if args.do_it:
                    gh_repo.edit(name=gh_repo.name, description=description)
                    print(
                        f"\tUpdated description, but there was a problem with issues in repo "
                        f"https://github.com/{org}/{repo}, pausing so you can fix, and then "
                        f"I'll archive for you.  (Press enter to archive, N and enter to skip)"
                    )
                    char = input()
                    if char not in ("n", "N"):
                        gh_repo.edit(name=gh_repo.name, archived=True)
                        if not args.quiet:
                            print(f"\tArchived repo {org}/{repo}")
                else:
                    if not args.quiet:
                        print(f"\tDid NOT archive {org}/{repo}")
    if args.show_report:
        print()
        print("\n".join(hook_report_list))
        print("---------------")
        print("\n".join(key_report_list))
        print("---------------")


if __name__ == "__main__":
    main()

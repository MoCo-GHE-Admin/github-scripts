#!/usr/bin/env python
"""
Script to look at an org, and output every users permissions to
the repos.  Including outside collab.
Useful for auditing who has access to what, and pointing out low handing
fruit for potential cleanup.
Note - github API reports perms for users as if the team is the user...
So there's no indication here if the perm is to the user or a team they
belong to.
"""

import argparse
import sys
from getpass import getpass

import alive_progress
from github3 import exceptions as gh_exceptions
from github3 import login

import utils

# Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 20


def parse_args():
    """
    Parse the command line.  Required commands is the name of the org
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(
        description="Depending on args, dump all repos in an org, repos for a user or users for a repo, and their user permissions, defaults to all repos and users in an org."
    )
    parser.add_argument("org", help="The org to examine", action="store")
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    analyse_group = parser.add_mutually_exclusive_group()
    analyse_group.add_argument("--user", help="Single user to examine in the org")
    analyse_group.add_argument("--repo", help="Single repo to examine in the org")
    # TODO: still required with alive-progress?
    parser.add_argument(
        "-i",
        action="store_true",
        default=False,
        dest="info",
        help="Give visual output of that progress continues - "
        "useful for long runs redirected to a file",
    )
    args = parser.parse_args()
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def list_to_str(input_list):
    """
    Given an input list, return a comma delimited string of the list items
    :param input_list: The list to work with
    :result: the comma delimited string
    """
    firstcol = True
    outstr = ""
    for item in input_list:
        if firstcol:
            outstr = str(item)
            firstcol = False
        else:
            outstr += f",{str(item)}"
    return outstr


def main():
    """
    Parse the args, connect to github, get the list of users in the org.
    Then go through the repos and update the users with usage counts.
    {user:{role: orgrole, team:count, repo:count}}
    leaving team in for now - but not updating it
    """
    args = parse_args()
    userlist = {}
    gh_sess = login(token=args.token)

    org = gh_sess.organization(args.org)
    # If a user was specified, just do that one, else, list all org members
    if args.user is None:
        memberlist = org.members(role="member")
    else:
        memberlist = [gh_sess.user(args.user)]
    for member in memberlist:
        userlist[member.login] = {
            "role": "member",
            "privpull": [],
            "privpush": [],
            "privadmin": [],
            "pubpull": [],
            "pubpush": [],
            "pubadmin": [],
        }

    if args.user is None:
        adminlist = org.members(role="admin")
        for admin in adminlist:
            userlist[admin.login] = {
                "role": "admin",
                "privpull": [],
                "privpush": [],
                "privadmin": [],
                "pubpull": [],
                "pubpush": [],
                "pubadmin": [],
            }

    # great, we have initialized our lists - now to go through the repos

    # If a repo is specified, just look at that one, otherwise all of them in the org.
    if args.repo is None:
        # TESTING
        # repolist = org.repositories(number=100)
        repolist = org.repositories()
    else:
        repolist = [gh_sess.repository(args.org, args.repo)]

    with alive_progress.alive_bar(manual=True, title="fetching list of repos") as bar:
        # materialize the iterator so we can get a count
        bar(0.1)
        repolist = list(repolist)
        bar(1)

    # FIXME Should I pull out "-ghsa-" repos - they NEVER find perms right.
    # Alternatively, just silently pass the NotFoundError?  (don't like that at first blush)
    with alive_progress.alive_bar(
        len(repolist), dual_line=True, title="getting repo permissions"
    ) as bar:
        for repo in repolist:
            bar.text = f"  - checking {repo.name}..."
            # print(f'DEBUG: repo: {repo.name}', file=sys.stderr)
            # TODO: have switch that decides iff the * prefix is added
            #      - messes with report_B(?)
            if repo.archived:
                repo_name = f"*{repo.name}"
            else:
                repo_name = repo.name
            try:
                repocollabs = repo.collaborators()
                for collaborator in repocollabs:
                    # print(f'collab: {collaborator.login}, repo: {repo.name}, '
                    # f'perms: {collaborator.permissions}', file=sys.stderr)
                    # go through and update their items
                    # External collabs aren't in the list already, so add them
                    if args.user is None or args.user == collaborator.login:
                        if collaborator.login not in userlist:
                            userlist[collaborator.login] = {
                                "role": "outside",
                                "privpull": [],
                                "privpush": [],
                                "privadmin": [],
                                "pubpull": [],
                                "pubpush": [],
                                "pubadmin": [],
                            }
                        if repo.private:
                            if collaborator.permissions["admin"]:
                                userlist[collaborator.login]["privadmin"].append(repo_name)
                            if collaborator.permissions["push"]:
                                userlist[collaborator.login]["privpush"].append(repo_name)
                            if collaborator.permissions["pull"]:
                                userlist[collaborator.login]["privpull"].append(repo_name)
                        else:
                            if collaborator.permissions["admin"]:
                                userlist[collaborator.login]["pubadmin"].append(repo_name)
                            if collaborator.permissions["push"]:
                                userlist[collaborator.login]["pubpush"].append(repo_name)
                            if collaborator.permissions["pull"]:
                                userlist[collaborator.login]["pubpull"].append(repo_name)
                utils.check_rate_remain(gh_sess, RATE_PER_LOOP, args.info)
                if args.info:
                    utils.spinner()
            except gh_exceptions.NotFoundError as err:
                print(
                    f"In repo {repo.name} and collab {collaborator.login} : {err.message}",
                    file=sys.stderr,
                )
            except gh_exceptions.ServerError:
                print(
                    f"50X error when processing repo: {repo_name} and collab {collaborator.login}"
                )
            bar()

    REPORT_B = True
    if REPORT_B:
        # per-repo report
        #   - makes it easier to see a user's permissions on each repo
        #   - could be used as input to tool that would replicate permissions between users

        # NOTES: misses archived repo perms due to the *NAME pattern in datastructure
        #   TODO: check for archived name or be ok with dropping those perms... seems sort of sane/safe

        # debugging
        print(userlist)

        # print header
        print("user,repo,role,access")

        # TODO: add gh org in output?

        # should only be one username...
        # TODO: complain (earlier) if more than one?
        for username, data in userlist.items():
            for repo in repolist:

                # if
                # perms = ""?
                # print f"{user},{repo},{perms}"

                access_string = ""
                tmp_list = []
                # print(list_to_str(data))

                # handle role
                access_level = ""
                if data["role"] == "member":
                    access_level = "member"
                elif data["role"] == "outside":
                    access_level = "outside"
                else:
                    raise "shouldn't be here"

                if repo.name in data["pubpull"]:
                    tmp_list.append("pubpull")
                if repo.name in data["pubpush"]:
                    tmp_list.append("pubpush")
                if repo.name in data["pubadmin"]:
                    tmp_list.append("pubadmin")
                if repo.name in data["privpull"]:
                    tmp_list.append("privpull")
                if repo.name in data["privpush"]:
                    tmp_list.append("privpush")
                if repo.name in data["privadmin"]:
                    tmp_list.append("privadmin")

                access_string = ",".join(tmp_list)

                if access_string != "":
                    print(f'{username},{repo.name},{access_level},"{access_string}"')
    else:
        # Print The Things.
        if args.info:
            print(file=sys.stderr)
        print(
            "Username, ORG Role, pub-count, priv-count, pub-pull, pub-push, pub-admin,"
            " priv-pull, priv-push, priv-admin"
        )
        for username, data in userlist.items():
            pubcount = len(data["pubpull"]) + len(data["pubpush"]) + len(data["pubadmin"])
            privcount = len(data["privpull"]) + len(data["privpush"]) + len(data["privadmin"])
            print(
                f'{username},{data["role"]},{pubcount},{privcount},"{list_to_str(data["pubpull"])}",'
                f'"{list_to_str(data["pubpush"])}","{list_to_str(data["pubadmin"])}",'
                f'"{list_to_str(data["privpull"])}","{list_to_str(data["privpush"])}",'
                f'"{list_to_str(data["privadmin"])}"'
            )


if __name__ == "__main__":
    main()

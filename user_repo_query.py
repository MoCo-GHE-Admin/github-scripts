#!/usr/bin/env python
"""
Script for removing a user/collaborator from org(s)
Given a GitHub ID, go through the list of orgs that the runner has access to
Look for orgs that the user is member of, as well as collaborator in.
Then extract and report the permissions that the user has.
"""


import sys

import alive_progress
from github3 import login
from github3.structs import GitHubIterator
from github3.users import ShortUser

from github_scripts import utils


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = utils.GH_ArgParser(
        description="Given a username - go through all orgs the caller has access to, to see what the username has access to."
    )
    parser.add_argument("username", help="User to examine")
    parser.add_argument(
        "--members",
        help="Should I look at membership in orgs, and not just collaborator status?",
        action="store_true",
    )
    parser.add_argument(
        "--orgs", nargs="+", help="List of orgs to check, else will look in orgs you belong to"
    )
    parser.add_argument(
        "--lineperorg",
        action="store_true",
        help="Instead of one repo per line, report one org per line",
    )
    args = parser.parse_args()
    return args


class OutsideCollabIterator(GitHubIterator):
    # based on work from hwine in mozilla/github-org-scripts/notebooks
    def __init__(self, org):
        super().__init__(
            count=-1,  # get all
            url=org.url + "/outside_collaborators",
            cls=ShortUser,
            session=org.session,
        )


def get_collabs(gh_sess, org):
    """
    Give me a list of all collabs in an org
    :param gh_sess: the github session
    :param org: An initialized org object
    result: list of all collabs
    """
    result = []
    for user in OutsideCollabIterator(org):
        utils.check_rate_remain(gh_sess)
        result.append(user.login.lower())
    return result


def look_for_user_in_org(gh_sess, org, username, bar):
    """
    Given and org and a username, output a dictionary of all repos that the user has perms to
    :param gh_sess: initialized github api sesssion
    :param org: an initialized org entry
    :param username: the GHid as a string
    :param bar: Progress bar to update
    :result: A dictionary of all initialized repos that the user belongs to
    Form of dict: (see below for initialization)
    """
    # Note that if there are custom levels, they will map to the closest one above it afaict.
    # i.e. if there's a form with all the READ, but a bit more, it will be LISTED as triage.
    resultdict = {"admin": [], "maintain": [], "push": [], "triage": [], "pull": []}
    if org.is_member(username):
        resultdict["member"] = True
    else:
        resultdict["member"] = False

    for repo in org.repositories():
        utils.check_rate_remain(gh_sess)
        bar.text(f"\t- {org.login}, {repo.name}")
        if repo.is_collaborator(username):
            for collab in repo.collaborators():
                utils.check_rate_remain(gh_sess)
                bar()
                if collab.login == username:
                    if collab.permissions["admin"]:
                        resultdict["admin"].append(repo.name)
                    elif collab.permissions["maintain"]:
                        resultdict["maintain"].append(repo.name)
                    elif collab.permissions["push"]:
                        resultdict["push"].append(repo.name)
                    elif collab.permissions["triage"]:
                        resultdict["triage"].append(repo.name)
                    else:
                        resultdict["pull"].append(repo.name)
    return resultdict


def output_org_based(permsdict):
    """
    Print out the perms in a nice CSV form
    :param permsdict: the dictionary of org:permission
    :result: printed CSV
    """
    # Note the change in output of "PUSH" -> "Write", and "PULL" -> "READ"
    print("Org,Member,Admin,Maintain,Write,Triage,Read")
    for org in permsdict.keys():
        print(
            f'"{org}", "{permsdict[org]["member"]}", "{",".join(permsdict[org]["admin"])}", "{",".join(permsdict[org]["maintain"])}", "{",".join(permsdict[org]["push"])}", "{",".join(permsdict[org]["triage"])}", "{",".join(permsdict[org]["pull"])}"'
        )


def output_repo_based(permsdict):
    """
    Print out the perms in a nice CSV form, based on one repo per line
    :param permsdict: the dictionary of org:permission
    :result: printed CSV
    """
    print("Org,Repo,Admin,Maintain,Write,Triage,Read")
    for org in permsdict.keys():
        for repo in permsdict[org]["admin"]:
            print(f"{org},{repo},TRUE,,,,")  # noqa: E231
        for repo in permsdict[org]["maintain"]:
            print(f"{org},{repo},,TRUE,,,")  # noqa: E231
        for repo in permsdict[org]["push"]:
            print(f"{org},{repo},,,TRUE,,")  # noqa: E231
        for repo in permsdict[org]["triage"]:
            print(f"{org},{repo},,,,TRUE,")  # noqa: E231
        for repo in permsdict[org]["pull"]:
            print(f"{org},{repo},,,,,TRUE")  # noqa: E231


def main():
    """
    Start the GH connection, get the orgs, and go through them,
    chronicalling what access the username has, and report.
    """

    args = parse_args()

    gh_sess = login(token=args.token)
    utils.check_rate_remain(gh_sess)

    orglist = []
    if args.orgs is not None:
        for orgname in args.orgs:
            orglist.append(gh_sess.organization(orgname))
    else:
        for org in gh_sess.organizations():
            orglist.append(org)

    with alive_progress.alive_bar(
        dual_line=True,
        title="Getting Perms",
        file=sys.stderr,
        length=20,
        force_tty=True,
        disable=False,
    ) as bar:
        permsdict = {}
        for org in orglist:
            utils.check_rate_remain(gh_sess)

            checkit = False  # Should we check this org for specific repo perms?
            bar.text(f"\t- {org.login}")
            bar()
            if org.is_member(args.username):
                if args.members:
                    checkit = True
            elif args.username in get_collabs(gh_sess, org):
                checkit = True
            if checkit:
                permsdict[org.login] = look_for_user_in_org(gh_sess, org, args.username, bar)

    # output(permsdict=permsdict)
    if args.lineperorg:
        output_org_based(permsdict=permsdict)
    else:
        output_repo_based(permsdict=permsdict)


if __name__ == "__main__":
    main()

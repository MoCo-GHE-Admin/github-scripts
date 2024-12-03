#!/usr/bin/env python
"""
Script to look at repos in an org, and dump the admin
"""

# TODO: Output only perms of ADMIN

import sys

import alive_progress
import github3
from github3 import exceptions as gh_exceptions

from github_scripts import utils

# noqa: E231

OWNERS = ["cknowles-admin", "moz-hwine", "ctbmozilla-admin", "aerickson-admin"]


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Report all admin permissions given to non-archived repos in an org, using restapi to aavoid undocumented rate limits"
    )
    parser.add_argument("org", type=str, help="The org to work with", action="store")
    parser.add_argument(
        "--repo",
        type=str,
        help="Specify a single repo to work on in the specified org if desired",
        action="store",
    )
    # parser.add_argument("--admin", help="Only output admins of the repo", action="store_true")
    args = parser.parse_args()
    return args


def main():
    """
    Query the list of repos for the permissions not given by teams.
    """
    args = parse_arguments()
    if args.repo is None:
        gh_sess = github3.login(token=args.token)
        org = gh_sess.organization(args.org)
        # repolist = {x for x in org.repositories()}
        repolist = org.repositories()
    else:
        repolist = [args.repo]

    output = {}

    with alive_progress.alive_bar(
        dual_line=True,
        title="Getting Perms",
        file=sys.stderr,
        length=20,
        force_tty=True,
        disable=False,
    ) as bar:
        for repo in repolist:
            try:
                utils.check_rate_remain(gh_sess=gh_sess, bar=bar)
                if not repo.archived:
                    # print(f"{repo=}")
                    bar.text = f" - checking {repo.full_name}..."
                    # repo = gh_sess.
                    output[repo.full_name] = set()
                    for user in repo.collaborators():
                        if user.permissions["admin"]:
                            if user.login not in OWNERS:
                                output[repo.full_name].add(user.login)
            except gh_exceptions.NotFoundError:
                # If this is a ghsa - this is expected, else scream and shout
                if repo.name.find("-ghsa-") == -1:
                    raise gh_exceptions.NotFoundError()

            bar()
    for repo in output.keys():
        print(f"{repo},{':'.join(output[repo])}")


if __name__ == "__main__":
    main()

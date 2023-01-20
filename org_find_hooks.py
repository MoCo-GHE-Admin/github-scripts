#!/usr/bin/env python
"""
Script to search for webhooks in repos in an org.
"""

import sys

import alive_progress
from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Parse the command line
    """
    parser = utils.GH_ArgParser(description="Search through an org for repos with webhooks")
    parser.add_argument("orgs", help="List of organizations that the repos belong to", nargs="+")
    parser.add_argument("--archived", help="Include archived repos", action="store_true")
    parser.add_argument(
        "--type",
        help="Type of repo, all (default), public, private",
        default="all",
        choices=["all", "public", "private"],
        dest="repo_type",
    )

    args = parser.parse_args()
    return args


def find_webhooks_in_org(gh_sess, org, repo_type, archived, bar):
    """
    Given an organization, return a list of found webhooks
    :param gh_sess: Active github session
    :param org: initialized org object
    :param repo_type: "all", "private", "public" for repo filtering
    :param archived: Boolean, include archived repos
    :param bar: initialized progress bar.
    :result: a list of strings with the hook information
    """
    foundhookslist = []

    bar.text = "  - Getting repositories"
    bar()
    repolist = org.repositories(type=repo_type)
    for repo in repolist:
        bar.text = f"  - Checking {repo.name}..."
        bar()
        if archived or not repo.archived:
            for hook in repo.hooks():
                foundhookslist.append(f"{org.name},{repo.name},{hook.config['url']},{hook.active}")
                utils.check_rate_remain(gh_sess=gh_sess, bar=bar)
    return foundhookslist


def main():
    """
    Search through the indicated org and repo types and report all webhooks found
    """
    args = parse_arguments()

    gh_sess = login(token=args.token)

    # with alive_progress.alive_bar(
    #     manual=True,
    #     title=f"Fetching list of {args.repo_type} repos in {args.org}",
    #     force_tty=True,  # force_tty because we are outputting to stderr now
    # ) as bar:
    #     repolist = list(repolist) #actualizing, so we get a count
    #     bar(1)

    header_str = "Org,Repo,Hook URL,Hook Active"
    foundhookslist = []

    for orgname in args.orgs:
        try:
            organization = gh_sess.organization(orgname)

            with alive_progress.alive_bar(
                dual_line=True,
                title=f"Searching for webhooks in {orgname}",
                file=sys.stderr,
                force_tty=True,  # force_tty because we are outputting to stderr now
            ) as bar:
                foundhookslist.extend(
                    find_webhooks_in_org(
                        gh_sess=gh_sess,
                        org=organization,
                        repo_type=args.repo_type,
                        archived=args.archived,
                        bar=bar,
                    )
                )
        except gh_exceptions.NotFoundError:
            print(
                f"Organization {orgname} not found - check spelling?  Continuing to next org if there is one.",
                file=sys.stderr,
            )

    print(header_str)
    print("\n".join(foundhookslist))


if __name__ == "__main__":
    main()

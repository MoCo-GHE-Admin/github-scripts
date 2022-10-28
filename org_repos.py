#!/usr/bin/env python
"""
Script for outputting all repos in an org
Used primarily as input to repo related scripts - allowing action on all or a subset of an org.
(poor person's rate limiting)
"""

from github3 import login

from github_scripts import utils


def parse_args():
    """
    Parse the command line.  Only required command is the name of the org.
    Detects if no PAT is given, asks for it.
    :return: Returns the parsed CLI datastructures.
    """

    parser = utils.GH_ArgParser(description="Gets a list of Repos for an Org.")
    parser.add_argument("org", help="The GH org to query", action="store", type=str)
    parser.add_argument(
        "--without-org",
        help="Include the org in the name, 'org/repo-name'",
        action="store_false",
        default=True,
        dest="with_org",
    )
    parser.add_argument(
        "--archived",
        help="Include archived repos.  Default is unarchived only.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--type",
        help="Type of repo: private, public, all.",
        default="all",
        choices=["public", "private", "all"],
    )
    args = parser.parse_args()
    return args


def main():
    """
    Go through the org, and output all repos, either 'org/repo' or just 'repo'
    Defaults to ignoring archived repos.
    The PAT needs READ to repos if only public are desired, but read/write
    if you want ALL the things.
    """

    args = parse_args()

    gh_sess = login(token=args.token)
    org = gh_sess.organization(args.org)
    if args.type == "all":
        repolist = org.repositories()
    elif args.type == "public":
        repolist = org.repositories(type="public")
    elif args.type == "private":
        repolist = org.repositories(type="private")
    else:
        raise Exception(f"{args.type} not a known repository visibility type")

    for repo in repolist:
        if (repo.archived and args.archived) or not repo.archived:
            if args.with_org:
                print(repo)
            else:
                print(repo.name)


if __name__ == "__main__":
    main()

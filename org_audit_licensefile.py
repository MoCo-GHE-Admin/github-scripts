#!/usr/bin/env python
"""
Script to perform a search of supplied orgs, and return the list of detected repo licenses.
"""

import argparse
import configparser
import sys
from datetime import datetime
from getpass import getpass

from github3 import exceptions as gh_exceptions
from github3 import login

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(
        description="given the org, look through all repos of type, and archive status and report on github detected licenses."
    )
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="*")
    parser.add_argument(
        "--archived",
        help="Include archived repos.  Default is unarchived only.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--type",
        help="Type of repo: private, public, all (Default).",
        default="all",
        choices=["public", "private", "all"],
    )
    parser.add_argument(
        "--include-URL",
        dest="url",
        action="store_true",
        help="Include the URL to the repo as a help for people analyzing things",
    )
    parser.add_argument(
        "--orgini",
        help='use "orglist.ini" with the "orgs" ' "entry with a csv list of all orgs to check",
        action="store_const",
        const="orglist.ini",
    )
    parser.add_argument(
        "--pat-key",
        default="admin",
        action="store",
        dest="patkey",
        help="key in .gh_pat.toml of the PAT to use",
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgini is None:
        raise Exception("You must specify either an org or an orgini")
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def munge_date(date_str):
    """
    Given the repolist created date string, give me a yyyy-mm-dd string
    param: date_str = 2021-07-06T15:04:04Z
    return: a string - 2021-07-06
    """
    format_str = "%Y-%m-%dT%H:%M:%SZ"
    date = datetime.strptime(date_str, format_str)
    return date.date().isoformat()


def main():
    """
    Taking in the query and list of orgs, run the search,
    print out the org name and the list of repos affected.
    """
    args = parse_arguments()
    resultlist = []
    # Read in the config if there is one
    orglist = []
    if args.orgini is not None:
        config = configparser.ConfigParser()
        config.read(args.orgini)
        orglist = config["GITHUB"]["orgs"].split(",")
    else:
        orglist = args.orgs

    gh_sess = login(token=args.token)
    linedict = {
        "org": "Org",
        "repo": "Repo",
        "created": "Created Date",
        "file": "Detected license file",
        "type": "License type",
    }
    if args.url:
        linedict["url"] = "URL"
    resultlist.append(linedict)
    for orgname in orglist:
        org = gh_sess.organization(orgname)
        # Get the list of repos
        if args.type == "all":
            repolist = org.repositories()
        elif args.type == "public":
            repolist = org.repositories(type="public")
        elif args.type == "private":
            repolist = org.repositories(type="private")
        else:
            raise Exception(f"{args.type} not a known repository visibility type")
        for repo in repolist:
            datestr = munge_date(repo.created_at)
            if (repo.archived and args.archived) or not repo.archived:
                try:
                    license = repo.license()
                except gh_exceptions.NotFoundError:
                    linedict = {
                        "org": f"{repo.owner}",
                        "repo": f"{repo.name}",
                        "created": datestr,
                        "file": "",
                        "type": "NO LICENSE DETECTED",
                    }
                else:
                    linedict = {
                        "org": f"{repo.owner}",
                        "repo": f"{repo.name}",
                        "created": datestr,
                        "file": license.name,
                        "type": license.license.name,
                    }
                if args.url:
                    linedict["url"] = f"{repo.html_url}"
                resultlist.append(linedict)
            utils.spinner()
            utils.check_rate_remain(gh_sess)
    # Time to print things
    print(file=sys.stderr)

    for line in resultlist:
        print(",".join(line.values()))


if __name__ == "__main__":
    main()

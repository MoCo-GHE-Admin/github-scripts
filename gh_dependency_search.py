#!/usr/bin/env python
"""
Script to perform a search of supplied orgs, returning the repo list
that return positives for a dependency of the specified language
"""

import argparse
from getpass import getpass

from gh_file_search import do_search
from github_scripts import utils

# data
language_default = "Python"
language_files = {
    "Python": [
        "requirements.txt",
        "pyproject.toml",
        "Pipfile",
    ],
    "Javascript": [
        "project.json",
    ],
}


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = argparse.ArgumentParser(description="Get file search resuls for a dependency")
    parser.add_argument(
        "--package", type=str, help="The package to search for.", action="store", required=True
    )
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="*")
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
    parser.add_argument(
        "-v",
        dest="verbose",
        help="Verbose - Print out that we're waiting for rate limit reasons",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-f",
        dest="print_file",
        help="Print out file level responses rather than repo level",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        dest="time",
        default=10,
        type=int,
        help="Time to sleep between searches, in seconds, should be 10s or more",
    )
    parser.add_argument(
        "--language",
        choices=language_files.keys(),
        default=language_default,
        help=f"Language to search for dependency, default is {language_default}",
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgini is None:
        raise Exception("You must specify either an org or an orgini")
    args.token = utils.get_pat_from_file(args.patkey)
    if args.token is None:
        args.token = getpass("Please enter your GitHub token: ")
    return args


def main():
    """
    Taking in the query and list of orgs, run the search,
    print out the org name and the list of repos affected.
    """
    args = parse_arguments()

    # just call gh_file_search.py with the defaults
    for file in language_files[args.language]:
        new_query = f"filename:{file} {args.package}"
        # rudely inject the query option and archive status
        args.query = new_query
        args.note_archive = True
        print(f"Searching for: {new_query}")
        do_search(args)


if __name__ == "__main__":
    main()

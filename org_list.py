#!/usr/bin/env python
"""
Script to list the organizations that the runner belongs to.
"""

from github3 import login

from github_scripts import utils


def parse_args():
    """
    Parse the command line.
    Detects if no PAT is given, asks for it.
    :return: Returns the parsed CLI datastructures.
    """

    parser = utils.GH_ArgParser(
        description="Gets a list of the organizations that the user belongs to.  Useful as input to scripts that take a list of orgs.  Note if you have personal orgs, this will be included."
    )
    parser.add_argument(
        "--owner", help="Get only the orgs that you have owner access to", action="store_true"
    )
    args = parser.parse_args()

    return args


def get_orgs(gh_sess, is_owner, bar=None):
    """
    Get the list of orgs of the user
    :param gh_sess: an initialized GH session
    :param is_owner: are we reporting only owner access?
    :param bar: alive_progress bar
    Return - returns list of org items
    """
    result_list = []
    if bar is not None:
        title = bar.title
        bar.title = "Looking for orgs"

    my_login = gh_sess.me().login

    for org in gh_sess.organizations():
        if bar is not None:
            bar.text = f" - Org {org.login}"
        if not is_owner:
            result_list.append(org)
        else:
            if my_login in [x.login for x in org.members(role="admin")]:
                result_list.append(org)
        if bar is not None:
            bar()
    if bar is not None:
        bar.title = title
    return result_list


def main():
    """Get the list of orgs"""
    args = parse_args()

    gh_sess = login(token=args.token)
    for org in get_orgs(gh_sess, args.owner):
        print(org.login)


if __name__ == "__main__":
    main()

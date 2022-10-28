#!/usr/bin/env python
"""
Script to manually poke the blocks/unblocks for orgs.
"""

import configparser

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Look at orgs, and either block or " "unblock the specified username"
    )
    parser.add_argument("username", type=str, help="The GH user name to block/unblock")
    parser.add_argument(
        "--block", help="should we block the user - default is unblock", action="store_true"
    )
    parser.add_argument("orgs", type=str, help="The org to work on", action="store", nargs="*")
    parser.add_argument(
        "--orgini",
        help='use "orglist.ini" with the "orgs" ' "entry with a csv list of all orgs to check",
        action="store_const",
        const="orglist.ini",
    )
    args = parser.parse_args()
    if args.orgs == [] and args.orgini is None:
        raise Exception("You must specify either an org or an orgini")
    return args


def blockuser(org, username, token, url="api.github.com"):
    """
    Block the user ffrom the org
    :param org: the organization
    :param user: the username to block
    :param token: the authorized token
    :param URL: the url of the API endpoint
    :return: true if successful - false if not.
    """
    headers = {"content-type": "application/json", "Authorization": "token " + token}
    query = f"https://{url}/orgs/{org}/blocks/{username}"
    request = requests.put(query, headers=headers)
    return request.status_code


def unblockuser(org, username, token, url="api.github.com"):
    """
    Unblock the user ffrom the org
    :param org: the organization
    :param user: the username to unblock
    :param token: the authorized token
    :param URL: the url of the API endpoint
    :return: true if successful - false if not.
    """
    headers = {"content-type": "application/json", "Authorization": "token " + token}
    query = f"https://{url}/orgs/{org}/blocks/{username}"
    request = requests.delete(query, headers=headers)
    return request.status_code


def main():
    """
    Read in the results, decide which path to take and call the needed block
    or unblock function
    """
    args = parse_arguments()
    # Read in the config if there is one
    orglist = []
    if args.orgini is not None:
        config = configparser.ConfigParser()
        config.read(args.orgini)
        orglist = config["GITHUB"]["orgs"].split(",")
    else:
        orglist = args.orgs

    for org in orglist:
        if args.block:
            actionstr = "blocked"
            result = blockuser(org, args.username, args.token)
        else:
            actionstr = "unblocked"
            result = unblockuser(org, args.username, args.token)

        # Per API docs, 204 is happy, 422 is already in blocklist

        if result == 204:
            print(f"User {args.username} was {actionstr} from org {org}")
        elif result == 422:
            print(
                f"Problem with {actionstr} action.  "
                f"Reason: {args.username} is already blocked in {org}"
            )
        else:
            print(
                f"Problem with blocking/unblocking {args.username} from org {org}"
                f"- status code for support: {result}"
            )


if __name__ == "__main__":
    main()

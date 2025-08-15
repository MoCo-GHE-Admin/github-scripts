#!/usr/bin/env python
"""
Script to add allowed action rules to a list of orgs.
Fail softly and continue if the org is already more permissive (i.e. allows all actions)
"""

import json

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Go through the list of orgs and remove the listed action rule from the org."
    )
    parser.add_argument("org", type=str, help="List of orgs to remove the action from", nargs="+")
    parser.add_argument(
        "--rule",
        type=str,
        help="REQUIRED: The rule to remove - ala 'ossf/scorecard@*' - should probably be quote delimited",
        required=True,
    )
    parser.add_argument("--api", type=str, help="The host of the API URL", default="api.github.com")
    args = parser.parse_args()
    return args


def get_org_allowed_actions(org, token, api):
    """
    Given an org and a token, grab the list of allowed actions
    :param: org: the organization name
    :param: token: The authentication token
    :param: api: the API URL base
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://{api}/orgs/{org}/actions/permissions/selected-actions"
    response = requests.get(url, headers=headers)
    existing_actions = None
    if response.status_code == 200:
        existing_actions = response.json().get("patterns_allowed", [])
    elif response.status_code == 409:
        print(f"For org {org}, all actions are permitted, no addition performed.")
    else:
        print(f"For org {org} the response was {response.status_code}, no addition performed")
    return existing_actions


def main():
    """
    Given the org and the action string to add, do the needful.
    """
    args = parse_arguments()
    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for org in args.org:
        current_actions = get_org_allowed_actions(org, args.token, args.api)
        if current_actions is not None:
            # Get add the new action to the list, and remove it from the org
            if args.rule not in current_actions:
                print(f"Rule {args.rule} is already removed from {org}, skipping")
            else:
                current_actions.remove(args.rule)
                url = f"https://{args.api}/orgs/{org}/actions/permissions/selected-actions"
                data = {"patterns_allowed": current_actions}
                response = requests.put(url=url, headers=headers, data=json.dumps(data))
                print(f"Remove record - {response.status_code=}")
                if response.status_code == 204:
                    print(f"Successfully removed {args.rule} from org {org}")
                else:
                    print(
                        f"Did not successfully remove from org {org} with status code {response.status_code}"
                    )


if __name__ == "__main__":
    main()

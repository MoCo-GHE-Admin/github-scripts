#!/usr/bin/env python
"""
Script to get the current action usage of all the orgs in the enterprise
"""

import sys

import alive_progress
import requests

import enterprise_org_list
from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Get action minutes usage of an enterprise, also estimates % of prepaid used by EOM"
    )
    parser.add_argument("enterprise", type=str, help="The enterprise to work on", action="store")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print ALL orgs, not just ones with action activity",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="only print out the totals, cancels verbose"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="the graphql URL",
        action="store",
        default="https://api.github.com/graphql",
    )
    args = parser.parse_args()
    return args


def get_billing_days_left(org, headers, url="api.github.com"):
    """
    Given and organization name, poke for the action minutes usage
    param org: organization name
    param headers: The headers and token for the request
    param url: the url for the rest api - defaults to "api.github.com"
    result: returns the days left in the billing cycle
    """
    query = f"https://{url}/orgs/{org}/settings/billing/shared-storage"
    result = requests.get(url=query, headers=headers)
    if result.status_code != 200:
        print(f"Error fetching data, result: {result.status_code}")
        exit()
    jsondata = result.json()
    return jsondata["days_left_in_billing_cycle"]


def get_actions_minutes(org, headers, url="api.github.com"):
    """
    Given and organization name, poke for the action minutes usage
    param org: organization name
    param headers: The headers and token for the request
    param url: the url for the rest api - defaults to "api.github.com"
    result: returns 3 element list - first element total minutes used, second: total paid minutes, third, total free minutes
    """
    query = f"https://{url}/orgs/{org}/settings/billing/actions"
    return_list = []
    result = requests.get(url=query, headers=headers)
    if result.status_code != 200:
        print(f"Error fetching data, result: {result.status_code}")
        exit()
    jsondata = result.json()
    return_list.append(jsondata["total_minutes_used"])
    return_list.append(jsondata["total_paid_minutes_used"])
    return_list.append(jsondata["included_minutes"])
    return return_list


def main():
    """
    Query github org and return the mapping of the SAML to GH login
    """
    args = parse_arguments()

    headers = {"content-type": "application/json", "Authorization": "Bearer " + args.token}

    orglist = enterprise_org_list.run_query(args.enterprise, headers, args.url)
    totalminutes = 0
    totalpaid = 0
    days_left = None
    included_minutes = None
    outputlist = {}
    # Get the Actions minutes for the orgs, and add them up.  and then present all non-zero
    # print("\n".join(orglist))
    # if not args.quiet:
    #     print("ORG,TOTAL,PAID")
    with alive_progress.alive_bar(
        dual_line=True,
        title="Examining action usage",
        file=sys.stderr,
        force_tty=True,
        disable=False,
    ) as bar:
        for org in orglist:
            bar.text = f"  - checking {org}..."
            if days_left is None:
                days_left = get_billing_days_left(org, headers)

            minutes = get_actions_minutes(org, headers)
            outputlist[org] = [minutes[0], minutes[1]]
            if included_minutes is None:
                included_minutes = minutes[2]
            totalminutes += minutes[0]
            totalpaid += minutes[1]
            bar()

    if not args.quiet:
        print("ORG,TOTAL,PAID")
        for org in outputlist:
            if (outputlist[org][0] != 0) or args.verbose:
                print(f"{org},{outputlist[org][0]},{outputlist[org][1]}")

    # We're estimating, so "All months are 31 days"
    # We're estimating, so we add 0.1 to the denominator to prevent UNDEF results
    # for a 100% usage month, this results in an error of ~0.3%
    # We just multiply the number of current minutes by the ratio of elapsed days and take the percentage
    total_ontrack = (totalminutes * (31 / (31 - days_left + 0.1))) / included_minutes
    print(f"TOTAL MINUTES = {totalminutes}")
    print(f"TOTAL PAID MINUTES = {totalpaid}")
    print(f"On track to hit {int(total_ontrack * 100)}% in {days_left} days")


if __name__ == "__main__":
    main()

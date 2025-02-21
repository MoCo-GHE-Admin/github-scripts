#!/usr/bin/env python
"""
Script to interpret a stream of json as copilot metrics.
https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-metrics?apiVersion=2022-11-28#get-copilot-metrics-for-an-enterprise
"""

import requests

from github_scripts import utils


def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """
    parser = utils.GH_ArgParser(
        description="Get top level copilot stats, including active user counts, and suggestions/acceptances usage"
    )
    parser.add_argument("enterprise", type=str, help="The enterprise to work on", action="store")
    parser.add_argument(
        "--url",
        type=str,
        help="the API hostname - defaults to api.github.com",
        action="store",
        default="api.github.com",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    headers = {"content-type": "application/json", "Authorization": "Bearer " + args.token}

    query = f"https://{args.url}/enterprises/{args.enterprise}/copilot/metrics"

    response = requests.get(url=query, headers=headers)

    if response.status_code != 200:
        print(f"Response code of {response.status_code}")
        exit()
    results = {}
    # a dict of dicts, keyed by day, with sub lists for active users, engaged users (?) and suggestions vs accepteds.
    # There's no indication in the API docs over what constitutes an active vs. engaged user.
    jsondata = response.json()
    # print(jsondata[0]["date"])
    for day in jsondata:
        results[day["date"]] = {
            "active": day["total_active_users"],
            "engaged": day["total_engaged_users"],
        }
        # print(day["copilot_ide_code_completions"]["editors"])
        suggest = 0
        accept = 0
        # Things in this metric rather than the old "here's the total" require you to add things up
        # Things are broken down by editor, model, and language.
        # Right now, we just care about TOTAL usage numbers.
        # But leaving the loops in place individually in case we want to add filtering for specifics
        for editors in day["copilot_ide_code_completions"]["editors"]:
            for models in editors["models"]:
                for languages in models["languages"]:
                    # Note, there's two different fields, unexplained - "code accepted" and "code acceptances"
                    # decided to go with acceptances, as that looks more like the previous data "total_acceptances_count"
                    accept += languages["total_code_acceptances"]
                    suggest += languages["total_code_suggestions"]
                    # accept += languages["total_code_lines_accepted"]
                    # suggest += languages["total_code_lines_suggested"]

        results[day["date"]]["acceptances"] = accept
        results[day["date"]]["suggestions"] = suggest
    print("Date, Total Suggestions, Total Acceptances, Active users")
    for day in results:
        print(
            f'{day},{results[day]["suggestions"]},{results[day]["acceptances"]},{results[day]["active"]}'
        )


if __name__ == "__main__":
    main()

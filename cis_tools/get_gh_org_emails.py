#!/usr/bin/env python3

import argparse
import pprint

from cis_tools import cis, github


def csv_report(gh_org):
    c = cis.CIS()
    org_member_login_to_id_hash = github.get_org_member_ids(gh_org)

    for gh_login in org_member_login_to_id_hash.keys():
        gh_id = org_member_login_to_id_hash[gh_login]
        users = c.get_users_from_gh_id(gh_id)
        if users:
            for user in users:
                print("%s,%s" % (gh_login, user.primary_email))
        else:
            print("%s,%s" % (gh_login, ""))


def print_org_email_report(gh_org):
    c = cis.CIS()
    org_member_login_to_id_hash = github.get_org_member_ids(gh_org)
    org_admins = github.get_org_admins(gh_org)

    no_cis_counter = 0
    total_counter = 0
    no_cis_arr = []

    for gh_login in org_member_login_to_id_hash.keys():
        gh_id = org_member_login_to_id_hash[gh_login]
        users = c.get_users_from_gh_id(gh_id)

        total_counter += 1
        is_admin = False

        if gh_login in org_admins:
            is_admin = True

        if users:
            for user in users:
                print("%s %s %s" % (gh_login, gh_id, user))
        else:
            print("%s %s NO_CIS_MATCH" % (gh_login, gh_id))
            if not is_admin:
                no_cis_counter += 1
                no_cis_arr.append(gh_login)
    print("---")
    print(
        "non-CIS-matched non-admin users / total users: %s/%s (%.1f%%) "
        % (
            no_cis_counter,
            total_counter,
            ((no_cis_counter / total_counter) * 100),
        )
    )
    print(
        "- non-cis non-admin (%s):\n %s"
        % (no_cis_counter, pprint.pformat(no_cis_arr, compact=True))
    )
    print(
        "- admins (%s):\n %s"
        % (len(org_admins), pprint.pformat(org_admins, compact=True))
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="display CIS emails for a GH org's members"
    )
    parser.add_argument("gh_org", help="a github org to inspect")
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode")
    # TODO: have a simple mode in between csv and verbose?
    args = parser.parse_args()

    if args.verbose:
        print_org_email_report(args.gh_org)
    else:
        csv_report(args.gh_org)

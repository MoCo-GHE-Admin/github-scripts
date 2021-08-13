#!/usr/bin/env python3

import argparse
import pprint

from cis_tools import cis

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="query CIS")
    parser.add_argument("--raw", "-r", action="store_true", help="show raw api data")
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="for non-raw queries, update CIS data first",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email", "-e", help="email address to search for")
    group.add_argument("--gh_v4", "-g", help="GH v4 ID to search for")
    group.add_argument("--cis_uuid", "-c", help="CIS UUID to search for")

    args = parser.parse_args()

    c = cis.CIS()

    if args.email:
        if args.update or args.raw:
            data = c.cis_primary_email_search(args.email)
        if args.raw:
            pprint.pprint(data)
        else:
            # TODO: implement as function in cis
            users = c.get_users_from_email(args.email)
            if args.update:
                for user in users:
                    c.decorate_user(user, data, force_update=True)
            for user in users:
                print(user)
    elif args.cis_uuid:
        if args.update or args.raw:
            data = c.cis_uuid_search(args.cis_uuid)
        if args.raw:
            pprint.pprint(data)
        else:
            print("not implemented")
    elif args.gh_v4:
        if args.update:
            print("update not supported with gh_v4 yet")
        if args.raw:
            print("raw query of gh v4 id not supported yet")
        else:
            users = c.get_users_from_gh_id(args.gh_v4)
            for user in users:
                print(user)
    else:
        raise Exception("shouldn't be here")

#!/usr/bin/env python
"""
Script for getting various org based statistics out of github.
"""

import argparse
from datetime import datetime
from getpass import getpass
from github3 import login

def parse_arguments():
    """
    Look at the first arg and handoff to the arg parser for that specific
    """

    parser = argparse.ArgumentParser(description="Get stats out of github about repos")
    parser.add_argument('operation', choices=['users','teams','commits'],
                        action='store')
    parser.add_argument('org', help="owner or org of the repo",
                        action='store', type=str)
    parser.add_argument('--repo', type=str, help='the repo to act upon',
                        action='store')
    parser.add_argument('--token', help='github token with perms to examine your repo',
                        action='store')
    parser.add_argument('--admin-only', help='for user and teams, only show admins',
                        default=False, action='store_true')
    parser.add_argument('--old-in-weeks', help='number of weeks to report as ''no activity''',
                        default=104, action='store', type=int, dest='old')
    args = parser.parse_args()
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def activity(gh_sess, org, age, printout=True):
    """
    go through the org and return a list of repos, with the date of their latest commit,
        or no commit
    :param gh_sess: an initialized github session
    :param org: the organization (or owner) name
    :param age: the age in weeks to consider (if no commits in that time, act as if no activity)
    :param printout: Print it out here - defaults True, if False, just return the list.
    :return: list, repo, created_date, last admin update, last push, last commit
    """
    repolist = gh_sess.repositories_by(org)
    commitlist = {}
    for short_repo in repolist:
        repo = short_repo.refresh()
        topdate = 0
        commits = repo.commit_activity(number=age)
        for week in commits:
            if week['total'] != 0:
                if week['week'] > topdate:
                    topdate = week['week']
        commitval = 0
        if topdate == 0:
            #no commits found, update list as apropos
            commitval = 'None'
        else:
            commitval = datetime.fromtimestamp(topdate)
        commitlist[repo.name] = {'created_at':datetime.fromisoformat(repo.created_at),
                                'updated_at':datetime.fromisoformat(repo.pushed_at),
                                'admin_update':datetime.fromisoformat(repo.updated_at),
                                'last_commit': commitval,
                                'archived':repo.archived}
    if printout:
        print("Repo, Created, Updated, Admin_update, Last_commit")
        for repo in commitlist.keys():
            if commitlist[repo]['archived']:
                print(f"{repo}, ARCHIVED")
            else:
                print(f"{repo},{commitlist[repo]['created_at']},{commitlist[repo]['updated_at']},"
                        f"{commitlist[repo]['admin_update']},{commitlist[repo]['last_commit']}")
            print(f"date-test - {repo['created_at'].strftime('%y-%m-%d')}")
    return commitlist

def main():
    """
    Main function for github repo_stats
    """
    args = parse_arguments()
    gh_session = login(token=args.token)

    # Figure out which option is called, and DO the thing
    if args.operation == 'commits':
        activity(gh_session, args.org, args.old)
        # repolist = gh_session.repositories_by(args.org)
        # for short_repo in repolist:
        #     repo = short_repo.refresh()
        #     print(f"Repo {repo.name} created: {repo.created_at}, last admin update:"\
        #         f"{repo.updated_at}, last push: {repo.pushed_at}")
        #     topdate = 0
        #     commits = repo.commit_activity(number=args.old)
        #     for week in commits:
        #         if week['total'] != 0:
        #             newdate = week['week']
        #             if newdate > topdate:
        #                 topdate = newdate
        #     #print(f"Last commit week - {datetime.datetime.fromtimestamp(topdate)}")
        #     if topdate == 0:
        #         #There was nothing found
        #         print(f"\tRepo {repo.name} had 0 commits in the last {args.old} weeks")
        #     else:
        #         print(f"\tRepo {repo.name} had a commit on"\
        #             f" {datetime.datetime.fromtimestamp(topdate)}")


if __name__ == '__main__':
    main()

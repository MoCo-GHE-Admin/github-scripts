#!/usr/bin/env python
"""
Script to look at an org, and parse out users with
little/no permissions to repos in the org
"""

import argparse
import sys
from time import sleep
from getpass import getpass
from github3 import login
from github3 import exceptions as gh_exceptions

def _create_char_spinner():
    """
    Creates a generator yielding a char based spinner.
    """
    while True:
        for char in '|/-\\':
            yield char


_spinner = _create_char_spinner()


def spinner(label=''):
    """
    Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stderr.write("\r%s %s" % (label, next(_spinner)))
    sys.stderr.flush()


def parse_args():
    """
    Parse the command line.  Required commands is the name of the org
    :return: Returns the parsed CLI datastructures.
    """

    parser = argparse.ArgumentParser(description=
                    "Gets a list of users for an org with how many repos they're involved with")
    parser.add_argument('org',
                    help = 'The org to examine',
                    action = 'store')
    parser.add_argument('--token', help = 'The PAT to auth with', action = 'store')
    parser.add_argument('--delay', help = 'delay between queries - rate '
                    'limits, default to 1, should never hit the limit',
                    action = 'store', type = float, default = 1.0)
    parser.add_argument('-i', action = 'store_true', default = False, dest = 'info',
                    help = 'Give visual output of that progress continues - '
                    'useful for long runs redirected to a file')
    args = parser.parse_args()
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def main():
    """
    Parse the args, connect to github, get the list of users in the org.
    Then go through the repos and update the users with usage counts.
    {user:{role: orgrole, team:count, repo:count}}
    leaving team in for now - but not updating it
    """
    args = parse_args()
    userlist = {}
    gh_sess = login(token=args.token)

    org = gh_sess.organization(args.org)
    memberlist = org.members(role='member')
    for member in memberlist:
        userlist[member.login] = {'role':'member','team':0, 'privrepo':0, 'pubrepo':0}
    adminlist = org.members(role='admin')
    for admin in adminlist:
        userlist[admin.login] = {'role':'admin','team':0, 'privrepo':0, 'pubrepo':0}

    # great, we have initialized our lists - now to go through the repos

    repolist = org.repositories()
    for repo in repolist:
        # print(f'DEBUG: repo: {repo.name}', file=sys.stderr)
        try:
            repocollabs = repo.collaborators()

            for collaborator in repocollabs:
                # go through and update their items
                # External collabs aren't in the list already, so add them
                if collaborator.login not in userlist:
                    if repo.private:
                        userlist[collaborator.login] = {'role':'outside', 'team':0,
                                                        'pubrepo':0, 'privrepo':1}
                    else:
                        userlist[collaborator.login] = {'role':'outside', 'team':0,
                                                        'pubrepo':1, 'privrepo':0}
                else:
                    if repo.private:
                        userlist[collaborator.login]['privrepo'] += 1
                    else:
                        userlist[collaborator.login]['pubrepo'] += 1
            if args.info:
                spinner()
            sleep(args.delay)
        except gh_exceptions.NotFoundError as err:
            print(f'In repo {repo.name} and collab {collaborator.login} : {err.message}',
                    file=sys.stderr)

    # Print The Things.
    print('Username, ORG Role, # of pubrepos with access, # of privrepos with access')
    for username, data in userlist.items():
        print(f'{username},{data["role"]},{data["pubrepo"]},{data["privrepo"]}')


if __name__ == '__main__':
    main()
 
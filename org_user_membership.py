#!/usr/bin/env python
"""
Script to look at an org, and parse out users with
little/no permissions to repos in the org
Split it out by push/pull/admin
"""

import argparse
import sys
from time import sleep
from getpass import getpass
from datetime import datetime
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

#Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 1.2

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
    parser.add_argument('-i', action = 'store_true', default = False, dest = 'info',
                    help = 'Give visual output of that progress continues - '
                    'useful for long runs redirected to a file')
    args = parser.parse_args()
    if args.token is None:
        args.token = getpass('Please enter your GitHub token: ')
    return args

def check_rate_remain(gh_sess, loopsize, update=False):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.  
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: Should we print a progress element to stderr
    """
    while gh_sess.rate_limit()['resources']['core']['remaining'] < loopsize:
        # Uh oh.
        if update:
            sleep(5)
            spinner()
        else:
            #calculate how long to sleep, sleep that long.
            refreshtime = datetime.fromtimestamp(
                gh_sess.rate_limit()['resources']['core']['reset'])
            now = datetime.now()
            naptime = (refreshtime-now).seconds
            print(f'Sleeping for {naptime} seconds', file=sys.stderr)
            sleep(naptime)

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
        userlist[member.login] = {'role':'member', 'privpull':[], 'privpush':[], 'privadmin':[],
                    'pubpull':[], 'pubpush':[], 'pubadmin':[]}
    adminlist = org.members(role='admin')
    for admin in adminlist:
        userlist[admin.login] = {'role':'admin', 'privpull':[], 'privpush':[], 'privadmin':[],
                    'pubpull':[], 'pubpush':[], 'pubadmin':[]}

    # great, we have initialized our lists - now to go through the repos

    repolist = org.repositories()
    # FIXME Should I pull out "-ghsa-" repos - they NEVER find perms right.
    # Alternatively, just silently pass the NotFoundError?  (don't like that at first blush)
    for repo in repolist:
        # print(f'DEBUG: repo: {repo.name}', file=sys.stderr)
        try:
            repocollabs = repo.collaborators()

            for collaborator in repocollabs:
                # print(f'collab: {collaborator.login}, repo: {repo.name}, perms: {collaborator.permissions}', file=sys.stderr)
                # go through and update their items
                # External collabs aren't in the list already, so add them
                if collaborator.login not in userlist:
                    userlist[collaborator.login] = {'role':'outside', 'privpull':[],
                                'privpush':[], 'privadmin':[], 'pubpull':[], 'pubpush':[],
                                'pubadmin':[]}
                else:
                    if repo.private:
                        if collaborator.permissions['admin']:
                            userlist[collaborator.login]['privadmin'].append(repo.name)
                        elif collaborator.permissions['push']:
                            userlist[collaborator.login]['privpush'].append(repo.name)
                        elif collaborator.permissions['pull']:
                            userlist[collaborator.login]['privpull'].append(repo.name)
                    else:
                        if collaborator.permissions['admin']:
                            userlist[collaborator.login]['pubadmin'].append(repo.name)
                        elif collaborator.permissions['push']:
                            userlist[collaborator.login]['pubpush'].append(repo.name)
                        elif collaborator.permissions['pull']:
                            userlist[collaborator.login]['pubpull'].append(repo.name)
            check_rate_remain(gh_sess, RATE_PER_LOOP, args.info)
            if args.info:
                spinner()
        except gh_exceptions.NotFoundError as err:
            print(f'In repo {repo.name} and collab {collaborator.login} : {err.message}',
                    file=sys.stderr)
        # except gh_exceptions.ServerError:
        #     print(f'50X error when processing repo: {repo.name} and collab {collaborator.login}')

    # Print The Things.
    print('Username, ORG Role, pub-count, priv-count, pub-pull, pub-push, pub-admin,'
            ' priv-pull, priv-push, priv-admin')
    for username, data in userlist.items():
        pubcount = len(data["pubpull"]) + len(data["pubpush"]) + len(data["pubadmin"])
        privcount = len(data["privpull"]) + len(data["privpush"]) + len(data["privadmin"])
        print(f'{username},{data["role"]},{pubcount},{privcount},"{data["pubpull"]}",'
            f'"{data["pubpush"]}","{data["pubadmin"]}","{data["privpull"]}","{data["privpush"]}",'
            f'"{data["privadmin"]}"')


if __name__ == '__main__':
    main()
 
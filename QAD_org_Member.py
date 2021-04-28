#!/usr/bin/env python
"""
Quick and dirty script to get membership lists for GHE
"""

from getpass import getpass
from github3 import login

def main():
    """
    prompt for PAT, then get the list of members for hte Mozilla org
    """
    pat = getpass("Enter your Personal Access Token: ")
    gh_session = login(token=pat)
    org = gh_session.organization('mozilla')
    memberlist = org.members()
    print("Github Login, Name, Email")
    for member in memberlist:
        fulluser = gh_session.user(member.login)
        print(f'{fulluser.login}, {fulluser.name}, {fulluser.email}')



if __name__ == '__main__':
    main()

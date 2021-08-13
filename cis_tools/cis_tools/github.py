#!/usr/bin/env python3

import os
import pprint
import sys

import github3
import toml
from github3 import login


def get_pat():
    home = os.path.expanduser("~")
    config_file_name = ".gh_pat.toml"
    if os.path.exists(config_file_name):
        config_file = config_file_name
    elif os.path.exists(os.path.join(home, config_file_name)):
        config_file = os.path.join(home, config_file_name)

    toml_blob = toml.load(config_file)
    pat = toml_blob["read_only"]
    return pat


def show_org_members(org_name):
    pat = get_pat()
    gh_sess = login(token=pat)
    org = gh_sess.organization(org_name)

    memberlist = org.members()  # do we want to specify a role? role='member'
    for member in memberlist:
        pprint.pprint(member)
        print(member.node_id)


def get_org_admins(org_name):
    """

    :param org_name:
    :return: arr of login ids
    """
    org_admins = []

    pat = get_pat()
    gh_sess = login(token=pat)
    org = gh_sess.organization(org_name)

    memberlist = org.members(role="admin")
    for member in memberlist:
        # pprint.pprint(member)
        # org_member_short_to_id[member.login] = member.node_id
        # print(member.node_id)
        org_admins.append(member.login)

    # pprint.pprint(org_member_short_to_id)
    return org_admins


def get_org_member_ids(org_name):
    """

    :param org_name:
    :return: hash
    """
    org_member_short_to_id = {}

    pat = get_pat()
    gh_sess = login(token=pat)
    try:
        org = gh_sess.organization(org_name)
    except github3.exceptions.NotFoundError as e:
        print("ERROR: gh reports no org by that name")
        print(e)
        sys.exit(1)

    memberlist = org.members()
    for member in memberlist:
        # pprint.pprint(member)
        org_member_short_to_id[member.login] = member.node_id
        # print(member.node_id)

    # pprint.pprint(org_member_short_to_id)
    return org_member_short_to_id


if __name__ == "__main__":
    print("mozilla-it:")
    pprint.pprint(get_org_member_ids("mozilla-it"))

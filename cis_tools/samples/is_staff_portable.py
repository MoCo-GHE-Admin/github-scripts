#!/usr/bin/env python3

import argparse
import pprint
import sys
from urllib.parse import quote

import requests
import toml

# fully portable example


def _get_cis_oauth_creds():
    # format for credential file should be:
    #
    # client_id = ""
    # client_secret = ""
    #
    # oauth app/credential needs the following scopes:
    #   DisplayAll
    #   ClassificationPublic
    #   - per https://mozilla-hub.atlassian.net/browse/IAM-829
    #
    toml_blob = toml.load(".cis_oauth.toml")
    return toml_blob


def get_cis_bearer_token():
    the_toml = _get_cis_oauth_creds()
    client_id = the_toml["client_id"]
    client_secret = the_toml["client_secret"]

    headers = {
        "content-type": "application/json",
    }
    data = (
        '{"client_id":"'
        + client_id
        + '","client_secret":"'
        + client_secret
        + '","audience":"api.sso.mozilla.com","grant_type":"client_credentials"}'
    )
    response = requests.post(
        "https://auth.mozilla.auth0.com/oauth/token",
        headers=headers,
        data=data,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print("failed to get access token")
        sys.exit(1)
    resp_data = response.json()
    return resp_data["access_token"]


# see https://github.com/mozilla-iam/cis/blob/master/docs/PersonAPI.md for additional query types
def cis_primary_email_search(email):
    """

    :param email:
    :return:
    """
    bearer_token = get_cis_bearer_token()
    url = (
        "https://person.api.sso.mozilla.com/v2/user/primary_email/{}?active=any".format(
            quote(email)
        )
    )
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    some_data = resp.json()
    return some_data


def is_user_staff(blob, verbose=False):
    """

    :param blob:
    :param verbose:
    :rtype: bool
    """

    # see https://mozilla-hub.atlassian.net/browse/IAM-829
    ldap_groups_indicating_staff = [
        "team_moco",
        "team_mofo",
        "team_pocket",
        "team_mozillaonline",
    ]

    try:
        ldap_data = blob["access_information"]["ldap"]["values"]
        if verbose:
            pprint.pprint(ldap_data)

        if ldap_data:
            user_groups = ldap_data.keys()
            for allowed_group in ldap_groups_indicating_staff:
                if allowed_group in user_groups:
                    return True
    except KeyError:
        print("is_user_staff: error parsing data: %s" % blob)
        return False
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="queries CIS LDAP group data to determine a user is mozilla staff"
    )
    parser.add_argument("email", help="email to query")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="display all LDAP groups found"
    )
    args = parser.parse_args()

    # query
    data = cis_primary_email_search(args.email)
    # check
    print(is_user_staff(data, verbose=args.verbose))

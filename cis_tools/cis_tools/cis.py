#!/usr/bin/env python3

import os
import pprint
from urllib.parse import quote

import peewee
import peeweext
import pendulum
import requests
import toml
from peeweext.fields import DatetimeTZField

# TODO: allow configuring this (via env var or ?)?
home = os.path.expanduser("~")
db_file_name = ".cis.db"
db_file_path = os.path.join(home, db_file_name)
db = peewee.SqliteDatabase(db_file_path)

VALID_CONNECTION_METHODS = ["github", "ad", "email", "oauth2", "google-oauth2"]


class User(peewee.Model):
    moz_iam_uuid = peewee.CharField(primary_key=True)
    primary_email = peewee.CharField(null=False)
    mozilla_ldap_primary_email = peewee.CharField(null=True)
    gh_v4_id = peewee.CharField(null=True)
    is_staff = peewee.BooleanField(default=False)
    # self.groups = ???

    # as used, it's the last time full details were retrieved
    last_updated = peeweext.fields.DatetimeTZField(null=True)

    # general cache of user's data...
    data = {}
    data_access_timestamp = peeweext.fields.DatetimeTZField(null=True)

    def __str__(self):
        return_str = ""
        return_str += "%s\n" % self.primary_email
        return_str += "  cis iam uuid: %s\n" % self.moz_iam_uuid
        if self.last_updated:
            return_str += "  last updated: %s ago (%s)\n" % (
                (self.last_updated.diff_for_humans(pendulum.now(), True)),
                self.last_updated,
            )
            return_str += (
                "  mozilla_ldap_primary_email: %s\n" % self.mozilla_ldap_primary_email
            )
            return_str += "  gh_v4_id: %s\n" % self.gh_v4_id
            return_str += "  is staff: %s" % self.is_staff
        else:
            return_str += "  last updated: never"

        return return_str

    class Meta:
        database = db


class CIS:
    def __init__(self):
        # maps email to request data
        self.email_to_data_cache = {}

        self._access_token = None
        self._access_token_last_refresh = None

    def _get_cis_oauth_creds(self):
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

        home = os.path.expanduser("~")
        config_file_name = ".cis_oauth.toml"
        if os.path.exists(config_file_name):
            config_file = config_file_name
        elif os.path.exists(os.path.join(home, config_file_name)):
            config_file = os.path.join(home, config_file_name)

        toml_blob = toml.load(config_file)
        return toml_blob

    def _get_cis_bearer_token(self):
        # TODO: support force_renew
        if (
            self._access_token
            and self._access_token_last_refresh
            and (self._access_token_last_refresh > pendulum.now().subtract(hours=4))
        ):
            # print("using cached auth token")
            return self._access_token
        # print("getting new auth token")

        the_toml = self._get_cis_oauth_creds()
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
            raise Exception("failed to get access token")
        data = response.json()

        self._access_token = data["access_token"]
        self._access_token_last_refresh = pendulum.now()
        return data["access_token"]

    def is_user_staff(self, blob, verbose=False):
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

    def get_users_from_gh_id(self, gh_id):
        try:
            return User.select().where(User.gh_v4_id == gh_id)
        except peewee.DoesNotExist:
            return None

    def get_users_from_email(self, email):
        try:
            return User.select().where(User.primary_email == email)
        except peewee.DoesNotExist:
            return None

    def get_email_from_gh_id(self, gh_id):
        user = self.get_users_from_gh_id(gh_id)
        if user:
            return self.get_users_from_gh_id(gh_id).primary_email
        return None

    def get_github_v4(self, blob):
        # pprint.pprint(data["identities"]["github_id_v4"]["value"])
        try:
            return blob["identities"]["github_id_v4"]["value"]
        except KeyError:
            return None

    def get_moz_iam_uuid(self, blob):
        return blob["uuid"]["value"]

    def get_full_name(self, blob):
        return blob["first_name"]["value"] + " " + blob["last_name"]["value"]

    def get_user_id(self, blob):
        # or do we want primary_username?
        # 'value': 'ad|Mozilla-LDAP|aerickson'},
        return blob["user_id"]["value"]

    def get_primary_email(self, blob):
        return blob["primary_email"]["value"]

    def get_mozilla_ldap_primary_email(self, blob):
        try:
            return blob["identities"]["mozilla_ldap_primary_email"]["value"]
        except KeyError as e:
            # print("get_mozilla_ldap_primary_email: KeyError %s" % e)
            # print(e)
            return None
        except Exception as e:
            pprint.pprint(blob)
            raise e

    def get_cis_data_cached(self, email):
        if email in self.email_to_data_cache:
            return self.email_to_data_cache[email]
        else:
            data = self.cis_primary_email_search(email)
            self.email_to_data_cache[email] = data
            return data
        raise Exception("shouldn't be here")

    # TODO: make this work, currently broken
    def cis_uuid_search(self, uuid):
        """

        :param uuid:
        :return:
        """
        bearer_token = self._get_cis_bearer_token()
        # /v2/user/uuid/<string:uuid>
        url = "https://person.api.sso.mozilla.com/v2/user/uuid/{}".format(quote(uuid))
        headers = {"Authorization": "Bearer {}".format(bearer_token)}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        some_data = resp.json()
        return some_data

    def cis_primary_email_search(self, email):
        """

        :param email:
        :return:
        """
        bearer_token = self._get_cis_bearer_token()
        url = "https://person.api.sso.mozilla.com/v2/user/primary_email/{}?active=any".format(
            quote(email)
        )
        headers = {"Authorization": "Bearer {}".format(bearer_token)}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        some_data = resp.json()
        return some_data

    def get_or_create_user_from_users_query_blob(self, blob):
        primary_email = self.get_primary_email(blob)
        iam_uuid = self.get_moz_iam_uuid(blob)

        # other fields are populated via full user query later

        # gh_v4_id = self.get_github_v4(blob)
        # is_staff = self.is_user_staff(blob)
        a_user, created = User.get_or_create(
            moz_iam_uuid=iam_uuid, defaults={"primary_email": primary_email}
        )
        # TODO: update last_updated? does last_updated mean full scan or just seen?
        a_user.save()
        return a_user, created

    # TODO: pull out printing/accounting into cis_tool or new function?
    def create_users_from_users_id_all_query(self):
        start_users = self.db_get_users()
        start_time = pendulum.now()
        seen_user_counter = {}
        for cm in VALID_CONNECTION_METHODS:
            seen_user_counter[
                cm
            ] = self.create_users_from_users_id_all_query_using_connection_method(cm)
        end_time = pendulum.now()
        end_users = self.db_get_users()
        # TODO: a created counter would be nice
        print("------------")
        print(
            "total seen users (over all connection methods): %s"
            % sum(seen_user_counter.values())
        )
        print("details: %s" % pprint.pformat(seen_user_counter, compact=True))
        print("users: before: %s, after: %s" % (start_users, end_users))
        print("scan time: %s" % end_time.diff_for_humans(start_time, True))

    # uses /v2/users/id/all (vs v2/users which gives full details)
    #
    # from https://github.com/mozilla-iam/cis/blob/3658d803e216b85e21540f6efa57cb1922741482/python-modules/cis_identity_vault/integration_tests/test_scan_speed.py
    #   connection_methods = ["github", "ad", "email", "oauth2", "google-oauth2"]
    #
    # does scanning all of these connection methods get the full set of all users?
    #  yes, or very close. found 65246 users with faster method out of 65261 in full db (probably includes inactives).
    def create_users_from_users_id_all_query_using_connection_method(
        self, connection_method
    ):
        # TODO: check that valid arg is passed
        if connection_method not in VALID_CONNECTION_METHODS:
            raise Exception("invalid connection method specified")

        bearer_token = self._get_cis_bearer_token()
        # first get the v4 id
        url = (
            "https://person.api.sso.mozilla.com/v2/users/id/all?connectionMethod=%s"
            % connection_method
        )
        headers = {"Authorization": "Bearer {}".format(bearer_token)}

        # fake data to allow loop entry
        data = ["nextPage"]
        seen_user_counter = 0
        page_counter = 0

        while "nextPage" in data:
            resp = requests.get(url, headers=headers)
            data = resp.json()
            # pprint.pprint(data)
            for user_dict in data["users"]:
                seen_user_counter += 1
                # print(user_dict)

                a_user, created = User.get_or_create(
                    moz_iam_uuid=user_dict["uuid"],
                    defaults={"primary_email": user_dict["primary_email"]},
                )
                # TODO: only full print the User if it was created?
                print(a_user)
                if created:
                    print("  created: True")
            if "nextPage" in data and data["nextPage"]:
                page_counter += 1
                print(data["nextPage"])
                pagination_id = data["nextPage"]["id"]
                url = (
                    "https://person.api.sso.mozilla.com/v2/users/id/all?connectionMethod=%s&nextPage={'id': '%s'}"
                    % (connection_method, pagination_id)
                )
            else:
                print("no data in nextPage")
                break

        print("users seen: %s" % seen_user_counter)
        print("page counter: %s" % page_counter)
        return seen_user_counter

    # NOTE: much slower than create_users_from_users_id_all_query()
    def create_users_from_users_query(self):
        bearer_token = self._get_cis_bearer_token()
        # first get the v4 id
        url = "https://person.api.sso.mozilla.com/v2/users"
        headers = {"Authorization": "Bearer {}".format(bearer_token)}
        resp = requests.get(url, headers=headers)
        data = resp.json()
        # pprint.pprint(data)
        users_enumerated_counter = 0
        try:
            for item in data["Items"]:
                users_enumerated_counter += 1
                a_user, _created = self.get_or_create_user_from_users_query_blob(item)
                print(a_user)
        except KeyError as e:
            pprint.pprint(data)
            raise e
        while "nextPage" in data:
            print("next page (already scanned %s users)..." % users_enumerated_counter)
            try:
                pagination_id = data["nextPage"]["id"]
            except TypeError as e:
                print(e)
                pprint.pprint(data)
                print("it looks like we're done...")
                # when we're out of users, we get 'TypeError: 'NoneType' object is not subscriptable'
                return
            url = (
                "https://person.api.sso.mozilla.com/v2/users?nextPage={'id': '%s'}"
                % pagination_id
            )
            resp = requests.get(url, headers=headers)
            data = resp.json()
            for item in data["Items"]:
                users_enumerated_counter += 1
                a_user, _created = self.get_or_create_user_from_users_query_blob(item)
                print(a_user)

    def decorate_email_user(self, primary_email, force_update=False):
        the_user = User.get(User.primary_email == primary_email)
        # pprint.pprint(the_user)
        data = self.cis_uuid_search(the_user.moz_iam_uuid)
        # pprint.pprint(data)
        self.decorate_user(the_user, data, force_update)
        print(the_user)

    def decorate_user(self, user, data, force_update=False):
        # if last_updated is within X, don't update
        if (
            not force_update
            and user.last_updated
            and user.last_updated > pendulum.now().subtract(hours=1)
        ):
            # print("not updating")
            return

        user.gh_v4_id = self.get_github_v4(data)
        user.is_staff = self.is_user_staff(data)
        user.mozilla_ldap_primary_email = self.get_mozilla_ldap_primary_email(data)
        user.last_updated = pendulum.now()
        user.save()

    def decorate_users(self, force_update=False, user_search_critera=None):
        if user_search_critera:
            # print("decorate_users: using user_search_critera")
            users = User.select().where(user_search_critera)
        else:
            users = User.select()

        users_count = users.count()
        counter = 0
        for user in users.iterator():
            counter += 1
            print("%s/%s: %s" % (counter, users_count, user.primary_email))
            data = self.cis_uuid_search(user.moz_iam_uuid)
            self.decorate_user(user, data, force_update)
            #     print("gh v4: %s" % c.get_github_v4(data))
            #     print("is staff: %s" % c.is_user_staff(data))
            print(user)
        print("decorate_users: done")

    def db_get_users(self):
        users = User.select()
        users_count = users.count()
        return users_count

    def decorate_mozilla_users(self, force_update=False):
        user_search_critera = User.primary_email.contains("mozilla")
        return self.decorate_users(
            force_update=force_update, user_search_critera=user_search_critera
        )

    def db_connect(self):
        db.connect()
        db.create_tables([User])


if __name__ == "__main__":
    c = CIS()
    c.db_connect()

    # search via email
    #
    # users = ["aerickson@mozilla.com", 'hwine@mozilla.com', "michelle@masterwayz.nl"]
    # for user in users:
    #     data = c.get_cis_data_cached(user)
    #     print("email: %s" % c.get_primary_email(data))
    #     print("cis iam uuid: %s" % c.get_moz_iam_uuid(data))
    #     print("gh v4: %s" % c.get_github_v4(data))
    #     print("is staff: %s" % c.is_user_staff(data))
    #     print("---")

    # search via uuid
    #
    # the_user = User.get(User.primary_email == 'aerickson@mozilla.com')
    # data = c.cis_uuid_search(the_user.moz_iam_uuid)
    # pprint.pprint(data)

    # credential testing
    #
    # print(c._get_cis_oauth_creds())
    # print(c._get_cis_bearer_token())
    # import sys; sys.exit()

    # enumerate users
    #
    # c.create_users_from_users_query()
    # populate fields for users with @mozilla.com emails, expand to all later...

    # decorating users
    #
    # c.decorate_users()
    # c.decorate_mozilla_users(force_update=False)
    # c.decorate_email_user("kmoir@mozilla.com")
    # c.decorate_email_user("hwine@mozilla.com")

    # investigating users with multiple CIS ids linked to same GH ID
    #
    # the_user = User.get(User.primary_email == "brian@polibyte.com")
    # print(the_user)
    # the_user = User.get(User.primary_email == "bpitts@mozilla.com")
    # print(the_user)

    # TODO: find out if mozilla_ldap_primary_email and primary_email ever differ
    # - run db search

    # print(c.db_get_users())

    # c.create_users_from_users_id_all_query_using_connection_method('github')
    # c.create_users_from_users_id_all_query_using_connection_method('ad')
    # c.create_users_from_users_id_all_query_using_connection_method("email")

    c.create_users_from_users_id_all_query()

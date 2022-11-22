"""
Helper file for code reuse throughout the github-scripts
"""
import argparse
import os
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

import requests
import toml

# Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 20


class GH_ArgParser(argparse.ArgumentParser):
    """
    Used to have some "Normal" things made standard across all github-scripts - token management being the first.
    """

    def __init__(self, *args, **kwargs):
        argparse.ArgumentParser.__init__(self, *args, **kwargs)
        self.add_argument(
            "--pat-key",
            default="admin",
            action="store",
            dest="patkey",
            help="key in .gh_pat.toml of the PAT to use",
        )
        self.add_argument("--token", help="use this PAT to access resources")

    def parse_args(self):
        args = super().parse_args()
        file_token = get_pat_from_file(args.patkey)
        if args.token is None:
            if file_token is None:
                args.token = getpass("Please enter your GitHub token: ")
            else:
                args.token = file_token
        return args


def get_pat_from_file(key_name="admin"):
    """
    Retrieve the personal access token from a file named .gh_pat.toml
    :param key_name: the toml key of the token in the file
    :result: either the PAT as a string or None

    pat file format:

    admin = "key1"
    read-only = "key2"
    key99 = "key99"
    """

    home = os.path.expanduser("~")
    config_file_name = ".gh_pat.toml"
    if os.path.exists(config_file_name):
        config_file = config_file_name
    elif os.path.exists(os.path.join(home, config_file_name)):
        config_file = os.path.join(home, config_file_name)
    else:
        return None

    # Get the last 3 octal digits of the perms from stat
    perm = oct(os.stat(config_file).st_mode)[-3:]
    if perm != "600":
        print("Err: .gh_pat.toml exists, but is NOT 600 perms", file=sys.stderr)
        return None

    try:
        toml_blob = toml.load(config_file)
        pat = toml_blob[key_name]
        return pat
    except Exception:
        return None


def check_rate_remain(gh_sess, loopsize=100, update=True, bar=None, search=False):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: should we print things letting you know what we're doing?
    :param bar: Are we using a progress bar?
    :param search: look at the search limits instead of API
    Note, we always print the "sleeping for XXX seconds"
    """
    # TODO: Look at making the naptime show that you're still making progress
    if search:
        limit_remain = gh_sess.rate_limit()["resources"]["search"]["remaining"]
    else:
        limit_remain = gh_sess.rate_limit()["resources"]["core"]["remaining"]
    while limit_remain < loopsize:
        # Uh oh.
        # calculate how long to sleep, sleep that long.
        if search:
            refreshtime = datetime.fromtimestamp(
                gh_sess.rate_limit()["resources"]["search"]["reset"]
            )
        else:
            refreshtime = datetime.fromtimestamp(gh_sess.rate_limit()["resources"]["core"]["reset"])
        now = datetime.now()
        # Set naptime to the time + a small fudge factor - 1/30 of the max reset time
        if search:
            naptime = (refreshtime - now).seconds + 2
        else:
            naptime = (refreshtime - now).seconds + 120
        if bar is None:
            print(
                f"API limits exhausted - sleeping for {naptime} seconds from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
                f"until {refreshtime.strftime('%Y-%m-%d %H:%M:%S')}",
                file=sys.stderr,
            )
        else:
            oldtitle = bar.text
            bar.text = (
                f"API limits exhausted - sleeping until {refreshtime.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        for timer in range(naptime):
            sleep(1)
            if update:
                if bar is not None:
                    bar()
        if update:
            if bar is None:
                print(file=sys.stderr)
                print("API timeout reset, continuing", file=sys.stderr)
            else:
                bar.text = oldtitle
            if search:
                limit_remain = gh_sess.rate_limit()["resources"]["search"]["remaining"]
            else:
                limit_remain = gh_sess.rate_limit()["resources"]["core"]["remaining"]


def check_graphql_rate_remain(
    token, loopsize=100, update=True, bar=None, url="https://api.github.com/graphql"
):
    """
    Given the token, and the size of the rate eaten by the loop, find the remaining graphql limits
    and if not enough remains, sleep until it is.
    :param token: The token to auth with
    :param loopsize: The amount of rate eaten by a run through things
    :param update: should we print things letting you know what we're doing?
    :param bar: Are we using a progress bar?
    :param url: the graphql URL to hit
    Note, we always print the "sleeping for XXX seconds"
    """

    query = """
{
    rateLimit {
        limit
        remaining
        resetAt
    }
}
    """
    headers = {"content-type": "application/json", "Authorization": "Bearer " + token}
    result = requests.post(url=url, json={"query": query}, headers=headers)
    remaining = result.json()["data"]["rateLimit"]["remaining"]
    timestring = result.json()["data"]["rateLimit"]["resetAt"].replace("Z", "+00:00")
    reset_time = datetime.fromisoformat(timestring)
    # reset_time = result.json()['data']['rateLimit']['resetAt']

    if remaining < loopsize:
        # Now we sleep
        now = datetime.now().astimezone()
        naptime = (reset_time - now).seconds + 10
        if bar is None:
            print(
                f"API limits exhausted - sleeping for {naptime} seconds from {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')} "
                f"until {reset_time.astimezone().strftime('%Y-%m-%d %H:%M:%S')}",
                file=sys.stderr,
            )
        else:
            oldtitle = bar.text
            bar.text = f"API limits exhausted - sleeping until {reset_time.astimezone().strftime('%Y-%m-%d %H:%M:%S')}"
        for timer in range(naptime):
            sleep(1)
            if update:
                if bar is not None:
                    bar()
        if update:
            if bar is None:
                print(file=sys.stderr)
                print("API timeout reset, continuing", file=sys.stderr)
            else:
                bar.text = oldtitle

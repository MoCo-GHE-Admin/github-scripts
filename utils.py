"""
Helper file for code reuse throughout the github-scripts
"""
import os
import sys
from datetime import datetime
from time import sleep

import toml


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


def _create_char_spinner():
    """
    Creates a generator yielding a char based spinner.
    """
    while True:
        for char in "|/-\\":
            yield char


_spinner = _create_char_spinner()


def spinner(label=""):
    """
    Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stderr.write("\r%s %s" % (label, next(_spinner)))
    sys.stderr.flush()


def check_rate_remain(gh_sess, loopsize=100, update=True):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: should we print things letting you know what we're doing?
    Note, we always print the "sleeping for XXX seconds"
    """
    # TODO: Look at making the naptime show that you're still making progress
    while gh_sess.rate_limit()["resources"]["core"]["remaining"] < loopsize:
        # Uh oh.
        # calculate how long to sleep, sleep that long.
        refreshtime = datetime.fromtimestamp(gh_sess.rate_limit()["resources"]["core"]["reset"])
        now = datetime.now()
        naptime = (refreshtime - now).seconds + 120
        print(
            f"API limits exhausted - sleeping for {naptime} seconds from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            f"until {refreshtime.strftime('%Y-%m-%d %H:%M:%S')}",
            file=sys.stderr,
        )
        for timer in range(naptime):
            sleep(1)
            if update:
                spinner()
        if update:
            print(file=sys.stderr)
            print("API timeout reset, continuing", file=sys.stderr)

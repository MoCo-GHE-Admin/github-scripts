"""
Helper file for code reuse throughout the github-scripts
"""
import os
import sys

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

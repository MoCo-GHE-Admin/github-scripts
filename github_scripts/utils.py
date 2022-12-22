"""
Helper file for code reuse throughout the github-scripts
"""
import argparse
import os
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

import alive_progress
import toml
from github3 import exceptions as gh_exceptions
from github3 import login

# Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 20


class GHPermsQuery:
    def __init__(self):
        self.gh_sess = None

    def init_gh_session(self, token):
        self.gh_sess = login(token=token)

    def update_userlist_with_permission_data(
        self, userlist, repolist, user=None, session_is_interactive=True, progress_disabled=False
    ):
        """
        Gather permissions information.
        :param userlist: Empty datastructure to use.
        :type userlist: Dict indexed by gh login. Values are dicts with keys that are permission types and values are lists of repos.
        :param repolist: Repos to check.
        :type repolist: List of github3.py repo objects.
        :param user: A specific user to inspect. If none, inspects all.
        :type user: github3.py user object, optional.
        :param session_is_interactive: Controls if GH API status messages are displayed.
        :type session_is_interactive: bool, optional.
        :param progress_disabled: Don't show progress bar.
        :type progress_disabled: bool, optional.
        """
        with alive_progress.alive_bar(
            len(repolist),
            dual_line=True,
            title="getting repo permissions",
            force_tty=True,
            disable=progress_disabled,
        ) as bar:
            for repo in repolist:
                bar.text = f"  - checking {repo.name}..."
                # print(f'DEBUG: repo: {repo.name}', file=sys.stderr
                if repo.archived:
                    repo_name = f"*{repo.name}"
                else:
                    repo_name = repo.name
                try:
                    repocollabs = repo.collaborators()
                    for collaborator in repocollabs:
                        # print(f'collab: {collaborator.login}, repo: {repo.name}, '
                        # f'perms: {collaborator.permissions}', file=sys.stderr)
                        # go through and update their items
                        # External collabs aren't in the list already, so add them
                        if user is None or user == collaborator.login:
                            if collaborator.login not in userlist:
                                userlist[collaborator.login] = {
                                    "role": "outside",
                                    "privpull": [],
                                    "privpush": [],
                                    "privadmin": [],
                                    "pubpull": [],
                                    "pubpush": [],
                                    "pubadmin": [],
                                }
                            if repo.private:
                                if collaborator.permissions["admin"]:
                                    userlist[collaborator.login]["privadmin"].append(repo_name)
                                if collaborator.permissions["push"]:
                                    userlist[collaborator.login]["privpush"].append(repo_name)
                                if collaborator.permissions["pull"]:
                                    userlist[collaborator.login]["privpull"].append(repo_name)
                            else:
                                if collaborator.permissions["admin"]:
                                    userlist[collaborator.login]["pubadmin"].append(repo_name)
                                if collaborator.permissions["push"]:
                                    userlist[collaborator.login]["pubpush"].append(repo_name)
                                if collaborator.permissions["pull"]:
                                    userlist[collaborator.login]["pubpull"].append(repo_name)
                    # re: update param: print updates about quota if running interactively
                    check_rate_remain(self.gh_sess, RATE_PER_LOOP, update=session_is_interactive)
                except gh_exceptions.NotFoundError as err:
                    print(
                        f"In repo {repo.name} and collab {collaborator.login} : {err.message}",
                        file=sys.stderr,
                    )
                except gh_exceptions.ServerError:
                    print(
                        f"50X error when processing repo: {repo_name} and collab {collaborator.login}",
                        file=sys.stderr,
                    )
                bar()
        return userlist


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


def _create_char_spinner():
    """
    Creates a generator yielding a char based spinner.
    """
    while True:
        for char in "|/-\\":
            yield char


_spinner = _create_char_spinner()
_last_label = None


def spinner(label="", end_spinner=False):
    """
    Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    global _last_label
    if _last_label != label:
        if _last_label is not None:
            sys.stderr.write("\n")
        _last_label = label
    sys.stderr.write("\r%s %s" % (label, next(_spinner)))
    if end_spinner:
        # we're done with the spinner, ensure that further output goes
        # to a new line
        sys.stderr.write("\n")
        _last_label = None
    sys.stderr.flush()


def check_rate_remain(gh_sess, loopsize=100, update=True, bar=None):
    """
    Given the session, and the size of the rate eaten by the loop,
    and if not enough remains, sleep until it is.
    :param gh_sess: The github session
    :param loopsize: The amount of rate eaten by a run through things
    :param update: should we print things letting you know what we're doing?
    :param bar: Are we using a progress bar?
    Note, we always print the "sleeping for XXX seconds"
    """
    # TODO: Look at making the naptime show that you're still making progress
    while gh_sess.rate_limit()["resources"]["core"]["remaining"] < loopsize:
        # Uh oh.
        # calculate how long to sleep, sleep that long.
        refreshtime = datetime.fromtimestamp(gh_sess.rate_limit()["resources"]["core"]["reset"])
        now = datetime.now()
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
                if bar is None:
                    spinner()
                else:
                    bar()
        if update:
            if bar is None:
                print(file=sys.stderr)
                print("API timeout reset, continuing", file=sys.stderr)
                spinner(end_spinner=True)
            else:
                bar.text = oldtitle


# cknowles description of get_top_perms()
#
# So, "privpull,privpush,privadmin" becomes "privadmin"
# "privpull,privpush" becomes "privpush"
# and "privpull" stays as it is.


def get_top_perm(perm_string):
    if "privadmin" in perm_string:
        return "privadmin"
    elif "pubadmin" in perm_string:
        return "pubadmin"
    elif "privpush" in perm_string:
        return "privpush"
    elif "pubpush" in perm_string:
        return "pubpush"
    elif "privpull" in perm_string:
        return "privpull"
    elif "pubpull" in perm_string:
        return "pubpull"
    else:
        # TODO: raise?
        return perm_string

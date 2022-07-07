import sys

import alive_progress
from github3 import exceptions as gh_exceptions
from github3 import login

import utils

# Roughly the number of github queries per loop.  Guessing bigger is better
RATE_PER_LOOP = 20


class GHQuery:
    def __init__(self):
        self.gh_sess = None

    def init_gh_session(self, token):
        self.gh_sess = login(token=token)

    # takes list of github3.py repo objects
    def update_userlist_with_permission_data(
        self, userlist, repolist, user=None, session_is_interactive=True, progress_disabled=False
    ):
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
                    utils.check_rate_remain(
                        self.gh_sess, RATE_PER_LOOP, update=session_is_interactive
                    )
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

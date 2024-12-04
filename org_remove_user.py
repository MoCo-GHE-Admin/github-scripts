#!/usr/bin/env python
"""
Script for removing a user/collaborator from org(s)
Given a username and a list of orgs, go through the orgs, and remove them as a member,
and then go through the repos, and remove them as outside collaborators.
"""

# Things to change if you want to use this
#   USER_PREFIX_LIST
#   USER_POSTFIX_LIST - these will likely be related to your organization, these are working entries for our setup.
#   CACHESIZE - The amount of hits (orgs) to cache the membership and OC queries for.
#   idp_handle - This prints out a link to removing a user forom our IDP ... you may do somethign else, modify for your needs

# TODO: Look at making an INI for the prefix/postfix lists

import email
import email.parser
import re
import sys
from email.policy import default
from functools import lru_cache

import alive_progress
import getch
from github3 import exceptions as gh_exceptions
from github3 import login
from github3.structs import GitHubIterator
from github3.users import ShortUser

import org_list
from github_scripts import utils

re_flags = re.MULTILINE | re.IGNORECASE

MAX_USABLE_USER = 10

CACHESIZE = 512

USER_PREFIX_LIST = ["moz", "moz-", "mozilla", "mozilla-", "admin-"]

USER_POSTFIX_LIST = ["moz", "-moz", "-admin"]


def parse_args():
    """
    Go through the command line.
    If no token is specified prompt for it.
    :return: Returns the parsed CLI datastructures.
    """
    parser = utils.GH_ArgParser(
        description="Go through all orgs your have owner status in and try to find any reference to the supplied user.  Either via provided GHID or with a file that has 'email: XXX@yyy.zzz' and 'Full name: XXX YYY' for guessing purposes"
    )
    parser.add_argument(
        "--ghid", help="GitHub ID of user to remove - other entries used for heuristics"
    )
    parser.add_argument(
        "--file", help="Data file with email and full name of the user for guessing purposes"
    )
    parser.add_argument("--email", help="email prefix (part before the @)")
    parser.add_argument("--fullname", help="User's full name, no quotes necessary", nargs="+")
    parser.add_argument("--orgs", help="Limit the examination to these orgs", nargs="+")
    parser.add_argument(
        "--doit",
        help="Perform the removals rather than talk about them - will give you links to do it if you prefer",
        dest="dry_run",
        action="store_false",
    )
    parser.add_argument("--verbose", help="Increase the verbosity of output", action="store_true")
    args = parser.parse_args()
    textitems = False  # Assume they didn't provide email/name in the command line
    # Make sure that the user has given us SOMETHING to guess with.  ghid, email, name, a file, etc.
    if args.email is not None or args.fullname is not None:
        if args.email is None or args.fullname is None:
            print("If you supply an email or name list on the command line, you must provide both")
            exit()
        textitems = True
    if args.ghid is None and args.file is None and not textitems:
        print(
            "You must supply either a GHID OR a file name OR the fullname/email on the command line"
        )
        exit()
    # Make sure all org names are consistently cased
    if args.orgs is not None:
        args.orgs = [x.lower() for x in args.orgs]
    return args


def parse_email(filename):
    """
    Extract email prefix and full name from in our case a saved email
    Param filename: The file to look at
    result: dict, with "email" and "names" (an ordered list of all the names you have)
    """
    msg = None
    result_dict = {}
    try:
        with open(filename, "rb") as f:
            msg = email.message_from_binary_file(f, policy=default)
    finally:
        if msg is None:
            print(f"Unable to read file {filename}")
            exit()
    simplest = msg.get_body(preferencelist=("plain", "html"))
    email_body = "".join(simplest.get_content().splitlines(keepends=True))

    match = re.search(r"^Full Name: (?P<full_name>\S.*)$", email_body, re_flags)
    if match:
        # Collect the full name as a list of individual names
        full_name = match.group("full_name")
        name_list = full_name.split()
    else:
        print("No full name found - is this an email with 'Full Name:' in it?")
        exit()
    match = re.search(r"^Email: (?P<primary_email>.*)@.*$", email_body, re_flags)
    if match:
        # Grab the before the @ as a name to check
        primary_email = match.group("primary_email") if match else None
    else:
        print("No email found - is this an email with 'Email:' in it?")
        exit()

    result_dict["email"] = primary_email
    result_dict["names"] = name_list
    return result_dict


def generate_guesses(namedict):
    """
    Given the namedict from the parse_file function, come up with a bunch of guesses for possible GHIDs
    Param: Namedict with "email" and "names" entries from the parse_email function.
    GlobalVar: userprefixlist, userpostfixlist - lists of values to pre and postfix to names for guessing purposes.
    result: list of possible entries.
    """

    guess_list = []
    # email is a good guess
    guess_list.append(namedict["email"])
    # Names concatenated is a good guess
    guess_list.append("".join(namedict["names"]))
    # People sometimes publish their full name
    guess_list.append(" ".join(namedict["names"]))

    # First/Last guess
    guess_list.append(namedict["names"][0] + namedict["names"][-1])
    # make guesses based on prefix/postfix list and email
    for pre in USER_PREFIX_LIST:
        guess_list.append(pre + namedict["email"])
    for post in USER_POSTFIX_LIST:
        guess_list.append(namedict["email"] + post)
    # everything with hyphens
    guess_list.append("-".join(namedict["names"]))
    # everything backwards with hyphens
    guess_list.append("-".join(namedict["names"][::-1]))
    # Backwards, no hyphens
    guess_list.append("".join(namedict["names"][::-1]))
    # If there's more than 2 names, backwards, last/first
    if len(namedict["names"]) > 2:
        guess_list.append(namedict["names"][0] + namedict["names"][-1])

    return guess_list


def find_login_guesses(gh_sess, guesslist):
    """
    Given a list of possibles, search through GitHub to see if there are users that match those guesses.
    param: gh_sess - an initialized github sessions
    param: guesslist - a list of potential names to check
    result: list of GH users that match something in the guesslist.
    """
    matchingusers = set()
    for guess in guesslist:
        # go through the guess list and see if there are any matches in any org we care about
        utils.check_rate_remain(gh_sess, loopsize=5, search=True)
        usersearch = gh_sess.search_users(guess)
        miniset = set()
        for searchresult in usersearch:
            miniset.add(searchresult.user.login)
        if len(miniset) > MAX_USABLE_USER:
            matchingusers.add(guess)
        else:
            matchingusers = matchingusers.union(miniset)

    return list(matchingusers)


@lru_cache(CACHESIZE)
class OutsideCollabIterator(GitHubIterator):
    # based on work from hwine in mozilla/github-org-scripts/notebooks
    def __init__(self, org):
        super().__init__(
            count=-1,  # get all
            url=org.url + "/outside_collaborators",
            cls=ShortUser,
            session=org.session,
        )


@lru_cache(CACHESIZE)
def get_collabs(org):
    """
    Give me a list of all collabs in an org
    :param org: An initialized org object
    result: list of all collabs
    """
    result = []
    for user in OutsideCollabIterator(org):
        result.append(user.login)
    return result


@lru_cache(CACHESIZE)
def get_members(org):
    """
    Get me a list of all members in an org.
    :param org: The initialized org object
    result: list of all members login names
    """
    result = []
    for user in org.members():
        result.append(user.login)
    return result


def is_collab(org, user):
    """
    Detect if the user is a collab in the org, and return True if so
    :param org: Initialized org object
    :param user: The GHID of the user
    :return boolean: True if we found someone.  False if not
    """
    found = False

    if user in get_collabs(org):
        found = True
    return found


def is_member(org, user):
    """
    Is the user a member of the org
    :param org: Initialized org object
    :param user: The GHID of the user
    :return boolean: True if we found someone.  False if not
    """
    found = False
    memberlist = get_members(org)
    if user in memberlist:
        found = True
    return found


def idp_handle(orglist):
    """
    GitHub SAML is terrifying.  If you remove a member but don't remove their ability to SAML from your own IDP,
    on re-SAMLing they'll succeed and their access is completly reinstated.  without any say so from anyone - so you HAVE to do IDP
    removal - Here at Moz, it's thing called "phonebook" - but you can edit this warning to match your needs.

    :param orglist: List of orgs to iterate through
    result: here we have it print to stdout, but with the dry-run flag you might have it actually do the remove
    """
    for org in orglist:
        print(
            f"\t** If SAMLd, remove from phonebook: https://people.mozilla.org/a/ghe_{org.lower()}_users/edit?section=members"
        )


def find_removable_user(orglist, login, bar=None):
    """
    Do the work to find the user in the orgs/repos
    param: orglist - list of organization instances to check
    param: login - GHID to look for
    param: bar - a progress bar
    result - dict - {member:[list of orgs they're members in], collab:[list of orgs they're collabs]}
    """
    resultdict = {"member": [], "collab": []}
    if bar is not None:
        bar.title = f"Looking for user {login} in orgs"
    for org in orglist:
        try:
            if bar is not None:
                bar.text = f" - Looking in org {org.login}"
            if is_member(org, login):
                resultdict["member"].append(org.login)
            elif is_collab(org, login):
                resultdict["collab"].append(org.login)
            bar()
        except gh_exceptions.NotFoundError:
            print(f"Org {org.login} not found, continuing")
    return resultdict


def remove_members(org, username):
    """
    Either print directions for removal for a member, OR do the removal
    :param org: initialized org object
    :param username: username to remove
    result: boolean, true on success
    """
    if org.remove_member(username):
        return True
    else:
        return False


def remove_collabs(org, username):
    """
    Either print directions for removal for a collaborator, OR do the removal
    :param org: initialized org object
    :param username: username to remove
    result: boolean, true on success
    """
    oc_url = org._json_data["issues_url"].replace("issues", "outside_collaborators")
    delete_url = oc_url + "/" + username
    response = org._delete(delete_url)
    if response.status_code not in [204]:
        return False
    else:
        return True


def report_and_handle_removal(gh_sess, found_removals, dry_run):
    """
    Look at the list of found things to remove, report on them, and if needed do the removal
    :param gh_sess: initialized Github session
    :param found_removals: dict of orgs under "user" in "members" and "collab" lists for the user.  {["users"]:{["member"]:[], ["collab"]:[]}}
    :param dry_run: if true, don't DO anything, just report
    result - prints out status, removed user if requested
    """
    for user, orglist in found_removals.items():
        if len(orglist["member"]) > 0 or len(orglist["collab"]) > 0:
            if orglist["member"] is not None:
                print(f"User {user} found as a member in - {' '.join(orglist['member'])}")
            if orglist["collab"] is not None:
                print(f"User {user} found as a collab in - {' '.join(orglist['collab'])}")
            print()
        # Having found removals - print out the IDP links for handling things.
        if len(orglist["member"]) > 0:
            idp_handle(orglist["member"])

        if (len(orglist["member"]) > 0 or len(orglist["collab"]) > 0) and not dry_run:
            print(
                f"Press Y to confirm removal of user {user} from your orgs, other key to continue without removal."
            )
            char = getch.getch()
            if char in ["Y", "y"]:
                for orgname in orglist["member"]:
                    org = gh_sess.organization(orgname)
                    if remove_members(org, user):
                        print(f"Removed {user} from {orgname}")
                    else:
                        print(f"Error removing {user} as a member from {orgname}")
                for orgname in orglist["collab"]:
                    org = gh_sess.organization(orgname)
                    if remove_collabs(org, user):
                        print(f"Removed OC {user} from {orgname}.")
                    else:
                        print(f"Was unable to remove {user} as a collab from {org}")

            else:
                print("continuing on")
        else:
            if len(orglist["member"]) > 0:
                print(f"{user} found as a member in the following orgs: {orglist['member']}")
                # TODO: have it print the links needed
            if len(orglist["collab"]) > 0:
                print(f"{user} found as a collaborator in the following orgs: {orglist['collab']}")


def main():
    """
    Start the GH connection, get the orgs, and go through them,
    removing members, and scanning outside collaborators
    """

    # dict of ["name"]:{["member"],["collab"]} with orgs in the appropriate slot
    found_removals = {}

    args = parse_args()

    # Login to Github, get the list of orgs you're an owner of.
    gh_sess = login(token=args.token)

    with alive_progress.alive_bar(
        dual_line=True,
        title="Searching for users",
        file=sys.stderr,
        force_tty=True,
        disable=False,
    ) as bar:
        # Get list of orgs that you have admin access to to search through
        utils.check_rate_remain(gh_sess=gh_sess, loopsize=300, bar=bar)
        orglist_to_check = org_list.get_orgs(gh_sess, True, bar)
        if args.orgs is not None:
            newlist = []
            for org in orglist_to_check:
                if org.login.lower() in args.orgs:
                    newlist.append(org)
            orglist_to_check = newlist
        if len(orglist_to_check) == 0:
            print("No valid orgs found that you have owner access to.")
            exit()

        # Figure out if we already know the GHID, or if we have to guess.
        namedict = {}
        loginlist = []
        # We're guessing - Get an email prefix and list of names
        if args.file is not None:
            namedict = parse_email(args.file)
        elif args.fullname is not None:
            namedict["email"] = args.email
            namedict["names"] = args.fullname
        if args.verbose:
            print(f"email and names: {namedict}")
        # If we're working with email/fullname do the guessing
        if args.file is not None or args.fullname is not None:
            name_guesses = generate_guesses(namedict)
            if args.verbose:
                print(f"names to guess with - {name_guesses}")
            utils.check_rate_remain(gh_sess=gh_sess, loopsize=400, bar=bar)
            loginlist = find_login_guesses(gh_sess=gh_sess, guesslist=name_guesses)
        if args.ghid is not None:
            # GHID provided, no guessing needed!
            loginlist.append(args.ghid)

        for loginname in loginlist:
            # Time to look for users in the list and pull them if desired.
            if loginlist.index(loginname) >= 1:
                utils.check_rate_remain(gh_sess=gh_sess, loopsize=400, bar=bar)
            found_things = find_removable_user(orglist_to_check, loginname, bar)
            found_removals[loginname] = found_things

    # Alright - we've found things - now let's report, and maybe remove
    print(f"List of discovered potential logins: {loginlist}")
    report_and_handle_removal(gh_sess=gh_sess, found_removals=found_removals, dry_run=args.dry_run)

    if args.verbose:
        collab_cache = get_collabs.cache_info()
        iterate_cache = OutsideCollabIterator.cache_info()
        member_cache = get_members.cache_info()
        print(f"Cache usage: {collab_cache=},\n{member_cache=},\n{iterate_cache=}")


if __name__ == "__main__":
    main()

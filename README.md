# GitHub-Scripts

A set of scripts for working with/analysis of github orgs/repos

## Requirements

This assumes you are on macOS Sequoia 15.2 (as of Jan 2025).

Python 3.13 is recommended. You can install this with [Homebrew](https://brew.sh/) or [pyenv](https://github.com/pyenv/pyenv).

Requirements are managed with Poetry (https://python-poetry.org/). If you installed Python with homebrew, install poetry with it as well. If you installed Python via pyenv, make sure your [shell environment is setup](https://github.com/pyenv/pyenv?tab=readme-ov-file#b-set-up-your-shell-environment-for-pyenv) and install poetry using pip (or similar).

Once poetry is installed, install the [Shell plugin](https://github.com/python-poetry/poetry-plugin-shell):
```
poetry self add poetry-plugin-shell
```

Then using poetry, start a shell session and install the dependencies:

```bash
# sources the virtualenv
poetry shell

# install dependencies
poetry install
```

## Naming
Starts with:
* "enterprise_" - operates on or across the enterprise."
* "gh_" - affects multiple orgs naturally.  (e.g. "How Much API rate is left")
* "org_" - limited to single orgs, occasionally multiple (e.g. "list all repos in ORG")
* "repo_" limited to just repos. (e.g. "Archive this repo")


## `enterprise_copilot_stats.py`
```
usage: enterprise_copilot_stats.py [-h] [--pat-key PATKEY] [--token TOKEN] [--url URL] enterprise

Get top level copilot stats, including active user counts, and suggestions/acceptances usage

positional arguments:
  enterprise        The enterprise to work on

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --url URL         the API hostname - defaults to api.github.com
```

## `enterprise_org_list.py`
```
usage: enterprise_org_list.py [-h] [--pat-key PATKEY] [--token TOKEN] [--url URL] enterprise

Get list of organizations in an enterprise

positional arguments:
  enterprise        The enterprise to work on

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --url URL         the graphql URL
```

## `gh_api_remain.py`
```
usage: gh_api_remain.py [-h] [--pat-key PATKEY] [--token TOKEN]

Print out the remaining API limits, and the time of the reset

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
```


## `gh_org_licenses.py`
```
usage: gh_org_licenses.py [-h] [--pat-key PATKEY] [--token TOKEN] [--pending] [--verbose] orgs [orgs ...]

Provided a list of orgs, output how many GHE licenses are required.

positional arguments:
  orgs              The orgs to work on

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --pending         Include Pending requests?
  --verbose         Output lists of members and ocs that are using license
  ```

## `gh_pat_owner.py`
```
usage: gh_pat_owner.py [-h] [--apihost APIHOST] [--raw] pat

Get details of a PAT, 'GH name, GH ID, Permissions'

positional arguments:
  pat                The PAT to analyze

optional arguments:
  -h, --help         show this help message and exit
  --apihost APIHOST  hostname to use for query - api.github.com is default
  --raw              Print out the raw results and headers
```

## `gh_user_moderation.py`
```
usage: gh_user_moderation.py [-h] [--pat-key PATKEY] [--token TOKEN] [--block] username orgs [orgs ...]

Look at orgs, and either block or unblock the specified username

positional arguments:
  username          The GH user name to block/unblock
  orgs              The org to work on

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --block           should we block the user - default is unblock
```

## `org_add_user.py`
```
usage: org_add_user.py [-h] [--pat-key PATKEY] [--token TOKEN] [--org ORG] [--user USERNAME] [--teams TEAMS [TEAMS ...]] [--owner]

Give a username, an org, and a team list and add the user to the org. NOTE: if the org is SAML'd you'll probably need to provision
the user in your IdP system(s)

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --org ORG             The org to work with
  --user USERNAME       GH user ID to add
  --teams TEAMS [TEAMS ...]
                        list of team slugs
  --owner               Should they be an owner
```

## `org_audit_licensefile.py`
```
usage: org_audit_licensefile.py [-h] [--pat-key PATKEY] [--token TOKEN] [--archived] [--type {public,private,all}] [--include-URL]
                                [orgs ...]

given the org, look through all repos of type, and archive status and report on github detected licenses.

positional arguments:
  orgs                  The org to work on

optional arguments:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --archived            Include archived repos. Default is unarchived only.
  --type {public,private,all}
                        Type of repo: private, public, all (Default).
  --include-URL         Include the URL to the repo as a help for people analyzing things
```

## `org_comms_team.py`
```
usage: org_comms_team.py [-h] [--pat-key PATKEY] [--token TOKEN] [--team-name TEAM_NAME] [--users USERS [USERS ...]] [--remove] org

Go into an org, create a team named for the --team-name and add all members to it, OR if --users is specified - add that list of
users. Specify --remove to invert the operation

positional arguments:
  org                   organization to do this to

optional arguments:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --team-name TEAM_NAME
                        name of the team to create, defaults to 'everybody-temp-comms'
  --users USERS [USERS ...]
                        List of users to add to the team
  --remove              Remove the specified users from the team rather than add
```

## `org_dependency_search.py`
NOTE - This relies on API searches, which GitHub is NOT advancing - you'll get better results using the WEBUI search
```
usage: org_dependency_search.py [-h] [--pat-key PATKEY] [--token TOKEN] [--archived] [--url URL] org package

Get the dependency for repos in an org

positional arguments:
  org               The 'org' to work on
  package           Package name to look for - must be the precise package name.

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --archived        Include archived repos
  --url URL         the graphql URL
```

## `org_find_hooks.py`
```
usage: org_find_hooks.py [-h] [--pat-key PATKEY] [--token TOKEN] [--archived] [--type {all,public,private}] orgs [orgs ...]

Search through an org for repos with webhooks

positional arguments:
  orgs                  List of organizations that the repos belong to

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --archived            Include archived repos
  --type {all,public,private}
                        Type of repo, all (default), public, private
```

## `org_find_keys.py`
```
usage: org_find_keys.py [-h] [--pat-key PATKEY] [--token TOKEN] [--archived] [--type {all,public,private}] orgs [orgs ...]

Search through an org for repos with keys

positional arguments:
  orgs                  List of organizations that the repos belong to

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --archived            Include archived repos
  --type {all,public,private}
                        Type of repo, all (default), public, private
```

## `org_list.py`
```
usage: org_list.py [-h] [--pat-key PATKEY] [--token TOKEN] [--owner]

Gets a list of the organizations that the user belongs to. Useful as input to scripts that take a list of orgs. Note if you have personal orgs, this will be included.

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --owner           Get only the orgs that you have owner access to
```

## `org_owners.py`
```
usage: org_owners.py [-h] [--pat-key PATKEY] [--token TOKEN] [orgs ...]

Look at orgs, and get the list of owners

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
```

## `org_remove_user.py`
```
usage: org_remove_user.py [-h] [--pat-key PATKEY] [--token TOKEN] [--ghid GHID] [--file FILE] [--email EMAIL] [--fullname FULLNAME [FULLNAME ...]] [--orgs ORGS [ORGS ...]] [--doit]
                          [--verbose]

Go through all orgs your have owner status in and try to find any reference to the supplied user. Either via provided GHID or with a file that has 'email: XXX@yyy.zzz' and 'Full name: XXX
YYY' for guessing purposes

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --ghid GHID           GitHub ID of user to remove - other entries used for heuristics
  --file FILE           Data file with email and full name of the user for guessing purposes
  --email EMAIL         email prefix (part before the @)
  --fullname FULLNAME [FULLNAME ...]
                        User's full name, no quotes necessary
  --orgs ORGS [ORGS ...]
                        Limit the examination to these orgs
  --doit                Perform the removals rather than talk about them - will give you links to do it if you prefer
  --verbose             Increase the verbosity of output
```

## `org_repo_perms`
```
usage: org_repo_perms.py [-h] [--pat-key PATKEY] [--token TOKEN] [--repo REPO]
                         [--all] [--admin] [--url URL]
                         org

Report all permissions given to repos to individuals (not by a team)

positional arguments:
  org               The org to work with

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --repo REPO       Specify a single repo to work on in the specified org if
                    desired
  --all             Dump ALL (Well, not owners) permissions, not just non-team
                    singletons
  --admin           Only output admins of the repo
  --url URL         the graphql URL
```

## `org_repo_perms_classic.py`
```
usage: org_repo_perms_classic.py [-h] [--pat-key PATKEY] [--token TOKEN] [--repo REPO] org

Report all admin permissions given to non-archived repos in an org, using restapi to avoid undocumented rate limits - edit OWNERS in source to exclude common users

positional arguments:
  org               The org to work with

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --repo REPO       Specify a single repo to work on in the specified org if desired

```

## `org_repos.py`
```
usage: org_repos.py [-h] [--pat-key PATKEY] [--token TOKEN] [--without-org] [--archived] [--type {public,private,all}] [--verbose] org

Gets a list of Repos for an Org.

positional arguments:
  org                   The GH org to query

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --without-org         Include the org in the name, 'org/repo-name'
  --archived            Include archived repos. Default is unarchived only.
  --type {public,private,all}
                        Type of repo: private, public, all.
  --verbose             Add a '*' to the output if the repo is archived
```

## `org_samlreport.py`
```
usage: org_samlreport.py [-h] [--pat-key PATKEY] [--token TOKEN] [--url URL] [-f OUTPUT] org

Get SAML account mappings out of a GitHub org

positional arguments:
  org               The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --url URL         the graphql URL
  -f OUTPUT         File to store CSV to
```

## `org_secret_alerts.py`
```
usage: org_secret_alerts.py [-h] [--pat-key PATKEY] [--token TOKEN] org

examine org for open security alerts from secret scanning, outputting csv data to pursue the alerts

positional arguments:
  org               The org that the repos are in

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
```

## `org_team_perms.py`
```
usage: org_repo_perms.py [-h] [--pat-key PATKEY] [--token TOKEN] [--repo REPO] [--all] [--url URL] org

Report all permissions given to repos to individuals (not by a team)

positional arguments:
  org               The org to work with

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --repo REPO       Specify a single repo to work on in the specified org if desired
  --all             Dump ALL (Well, not owners) permissions, not just non-team singletons
  --url URL         the graphql URL
```

## `org_teams.py`
```
usage: org_teams.py [-h] [--pat-key PATKEY] [--token TOKEN] [--team TEAM] [--unmark] org

Gets a list of teams and their users for an Org. Users with '*' are maintainers of the team, reports using the team-slug

positional arguments:
  org               The GH org to query

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --team TEAM       The team slug to dump - if specified will ONLY use that team. (slug, NOT name)
  --unmark          Do not mark maintainers in the list
```

## `repo_active_users.py`
```
usage: repo_active_users.py [-h] [--pat-key PATKEY] [--token TOKEN] [--days DAYS] [--author] [--debug] org repos [repos ...]

Gets a list of active users for a list of reposAlso checks wiki for activity, and can be told to check for issues activity.

positional arguments:
  org               The organization that the repos belong to
  repos             list of repos to examine - or use --file for file base input

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --days DAYS       How many days back to look, default, 30
  --author          Use the author rather than committer email, if you're concerned about people with permissions, committer is what
                    you want
  --debug
```

## `repo_activity.py`
```
usage: repo_activity.py [-h] [--pat-key PATKEY] [--token TOKEN] [--org ORG] [--date DATE] [--issues] [--ignore-wiki] [--archived] [--file FILE] [repos ...]

Gets a latest activity for a repo or list of repos. Also checks wiki for activity, and can be told to check for issues activity.

positional arguments:
  repos             list of repos to examine - or use --file for file base input

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --org ORG         Look at all the repos in the org, will ignore archived repos by default
  --date DATE       YYYYMMDD, ignore anything with update date after this date.
  --issues          Check the issues to set a date of activity if more recent than code
  --ignore-wiki     Don't do the wiki analysis
  --archived        if doing org level, should we include archived repos?
  --file FILE       File of 'owner/repo' names, 1 per line
```

## `repo_add_perms.py`
```
usage: repo_add_perms.py [-h] [--pat-key PATKEY] [--token TOKEN] --perm PERM --org ORG --repos REPOS [REPOS ...] [--apihost APIHOST]
                         {team,member} name

invite member or team to specified repos at specified level. If adding a user, if the user is a member, adds the member, else invites
as an OC.

positional arguments:
  {team,member}         team or member - specify type of perm
  name                  Name of the member or team to add

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --perm PERM           String of the role name, defaults are 'pull'(read), 'push'(write), 'triage', 'maintain', 'admin' - but others
                        can be set by the repo admin. If set wrongly, you'll get a 422 error
  --org ORG             Organization/owner that the repos belong to
  --repos REPOS [REPOS ...]
                        list of repo names
  --apihost APIHOST     API host to connect to - default api.github.com
```

## `repo_archiver.py`
```
usage: repo_archiver.py [-h] [--pat-key PATKEY] [--token TOKEN] [--inactive] [--custom CUSTOM] [--file FILE] [--disable-report]
                        [--ignore-issue-label] [--pause] [-q] [--doit]
                        [repos ...]

Archive the specified repo, labelling and then closing out issues and PRs, per GitHub best practices. Closed issues/PRs, and description/topic
changes can be completely reversed using the repo_unarchiver script. DEFAULTS to dry-run and will not modify things until --doit flag is applied.
Also, will report on any existing hooks or keys in the repos so that cleanup in related systems can occur

positional arguments:
  repos                 owner/repo to archive

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --inactive            Change the 'abandoned' and 'deprecated' wording to 'inactive'
  --custom CUSTOM       Custom text to add to issue/PR label, and description, less than 36 char long
  --file FILE           File with "owner/repo" one per line to archive
  --disable-report      Disable the hook/keys report at the end of the process.
  --ignore-issue-label  Ignore the existence of the ARCHIVED issue label
  --pause               Pause upon detecting anomalies that might need fixing, but aren't blockers
  -q                    DO NOT print, or request confirmations
  --doit                Actually perform the archiving steps
```

## `repo_close_issues.py`
```
usage: repo_close_issues.py [-h] [--pat-key PATKEY] [--token TOKEN] [--close-pr] [--comment COMMENT] [--doit] [--delay DELAY]
                            org repo

Close issues associated with the specified repo. Do not close PRs unless specified, and only do things if specified

positional arguments:
  org                Org/owner name
  repo               Name of the repo

optional arguments:
  -h, --help         show this help message and exit
  --pat-key PATKEY   key in .gh_pat.toml of the PAT to use
  --token TOKEN      use this PAT to access resources
  --close-pr         Close the PRs too?
  --comment COMMENT  A comment to close the issue with
  --doit             Actually close things
  --delay DELAY      seconds between close requests, to avoid secondary rate limits > 1
```

## `repo_issue_create.py`
```
usage: repo_issue_create.py [-h] [--pat-key PATKEY] [--token TOKEN] --conf CONF [--reopen] [--always-comment] repos [repos ...]

Given a list of org/repos, open an issue in each based on the settings in the conf yaml file. If update is specified, will reopen
closed issues, and add a comment to any found issues of the same bodyUID field

positional arguments:
  repos             The repos to work on as org/repo space delimited

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --conf CONF       The yaml file to use - see issueconf.yaml.example
  --reopen          Should we reopen closed issues?
  --always-comment  Always add the comment, even if it already exists.
```

## `repo_team_singleton_audit.py`
```
usage: repo_team_singleton_audit.py [-h] [--pat-key PATKEY] [--token TOKEN] --repos REPOS [REPOS ...] [--url URL] org

Look through repos for permissions given not by a team (a singleton)

positional arguments:
  org                   The org to work with

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --repos REPOS [REPOS ...]
                        The repos to work on in the specified org
  --url URL             the graphql URL
```

## `repo_unarchiver.py`
```
usage: repo_unarchiver.py [-h] [--pat-key PATKEY] [--token TOKEN] [-q] repo

Reverse archival closing of issues of the specified repo, Note, repo MUST be manually unarchived before this script

positional arguments:
  repo              owner/repo to unarchive

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  -q                DO NOT print, or request confirmations
```

## `user_repo_query.py`
```
usage: user_repo_query.py [-h] [--pat-key PATKEY] [--token TOKEN] [--members] [--orgs ORGS [ORGS ...]] [--lineperorg] username

Given a username - go through all orgs the caller has access to, to see what the username has access to.

positional arguments:
  username              User to examine

options:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --members             Should I look at membership in orgs, and not just collaborator status?
  --orgs ORGS [ORGS ...]
                        List of orgs to check, else will look in orgs you belong to
  --lineperorg          Instead of one repo per line, report one org per line
```

# Deprecated
Scripts that are, for one reason or another no longer commonly or accurately functional, largely kept in the hopes that GitHub fixes underlying problems, and as example code.

## `enterprise+action_check.py`
With the advent of enhanced billing - the old API targets used here, while still "working" return 0.  We're working with GitHub support to figure out if the new API targets will allow us to get this information.
```
usage: enterprise_action_check.py [-h] [--pat-key PATKEY] [--token TOKEN] [-v] [-q] [--url URL] enterprise

Get action usage of an enterprise, also estimates % of prepaid used by EOM

positional arguments:
  enterprise        The enterprise to work on

options:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  -v, --verbose     Print ALL orgs, not just ones with action activity
  -q, --quiet       only print out the totals, cancels verbose
  --url URL         the graphql URL
```

## `gh_dependency_search.py`
This has been superceded by the org_dependency_search
NOTE - This relies on API searches, which GitHub is NOT advancing - you'll get better results using the WEBUI search
```
usage: gh_dependency_search.py [-h] [--pat-key PATKEY] [--token TOKEN] --package PACKAGE [-v] [-f] [-t TIME]
                               [--language {Python,Javascript}]
                               [orgs ...]

Get file search resuls for a dependency

positional arguments:
  orgs                  The org to work on

optional arguments:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --package PACKAGE     The package to search for.
  -v                    Verbose - Print out that we're waiting for rate limit reasons
  -f                    Print out file level responses rather than repo level
  -t TIME               Time to sleep between searches, in seconds, should be 10s or more
  --language {Python,Javascript}
                        Language to search for dependency, default is Python
```

## `gh_file_search.py`
NOTE - This relies on API searches, which GitHub support informs me do not return reliable information.  Recommendation from them, use the WEBUI, OR pay for GHAS and use vulnerability scanning to find concerning code
```
usage: gh_file_search.py [-h] [--pat-key PATKEY] [--token TOKEN] --query QUERY [--note-archive] [-v] [-f] [-t TIME]
                         [orgs ...]

Get file search results for an org, returning repo list. e.g. if you want 'org:<ORGNAME> filename:<FILENAME> <CONTENTS>', then you
just need 'filename:<FILENAME> <CONTENTS>' and then list the orgs to apply it to. Note: There's a pause of ~10 seconds between org
searches due to GitHub rate limits - add a -v if you want notice printed that it's waiting

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --query QUERY     The query to run, without orgs
  --note-archive    if specified, will add archival status of the repo to the output, this will slow things down and use more API
                    calls
  -v                Verbose - Print out that we're waiting for rate limit reasons
  -f                Print out file level responses rather than repo level
  -t TIME           Time to sleep between searches, in seconds, should be 10s or more
```


# Supporting files

## `.gh_pat.toml`
Used to store PAT files - used by several of the scripts.
Can be either in the repo directory or homedir.
Should be 600 permissions.
```
admin = "PAT1"
read-only = "PAT2"
key99 = "PAT99"

```

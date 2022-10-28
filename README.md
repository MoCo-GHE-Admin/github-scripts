# GitHub-Scripts

A set of scripts for working with/analysis of github orgs/repos

## Requirements

Requirements are managed with Poetry (https://python-poetry.org/).

Once poetry is installed, you can set up the repo.

```bash
# sources the virtualenv
poetry shell

# install dependencies
poetry install
```

## Naming
Starts with:
* "gh_" - affects multiple orgs naturally.  (e.g. "How Much API rate is left")
* "org_" - limited to single orgs, occasionally multiple (e.g. "list all repos in ORG")
* "repo_" limited to just repos. (e.g. "Archive this repo")

## `gh_api_remain.py`
```
usage: gh_api_remain.py [-h] [--pat-key PATKEY] [--token TOKEN]

Print out the remaining API limits, and the time of the reset

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
```

## `gh_dependency_search.py`
```
usage: gh_dependency_search.py [-h] [--pat-key PATKEY] [--token TOKEN] --package PACKAGE [--orgini] [-v] [-f] [-t TIME]
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
  --orgini              use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  -v                    Verbose - Print out that we're waiting for rate limit reasons
  -f                    Print out file level responses rather than repo level
  -t TIME               Time to sleep between searches, in seconds, should be 10s or more
  --language {Python,Javascript}
                        Language to search for dependency, default is Python
```

## `gh_file_search.py`
```
usage: gh_file_search.py [-h] [--pat-key PATKEY] [--token TOKEN] --query QUERY [--note-archive] [--orgini] [-v] [-f] [-t TIME]
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
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  -v                Verbose - Print out that we're waiting for rate limit reasons
  -f                Print out file level responses rather than repo level
  -t TIME           Time to sleep between searches, in seconds, should be 10s or more
```

## `gh_org_licenses.py`
```
usage: gh_org_licenses.py [-h] [--pat-key PATKEY] [--token TOKEN] [--pending] [--orgini] [orgs ...]

Provided a list of orgs, output how many GHE licenses are required.

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --pending         Include Pending requests?
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
```

## `gh_org_repo_perms.py`
```
usage: gh_org_repo_perms.py [-h] [--pat-key PATKEY] [--token TOKEN] [--user USER | --repo REPO] org

Depending on args, dump all repos in an org, repos for a user or users for a repo, and their user permissions, defaults to all repos
and users in an org.

positional arguments:
  org               The org to examine

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --user USER       Single user to examine in the org
  --repo REPO       Single repo to examine in the org
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
usage: gh_user_moderation.py [-h] [--pat-key PATKEY] [--token TOKEN] [--block] [--orgini] username [orgs ...]

Look at orgs, and either block or unblock the specified username

positional arguments:
  username          The GH user name to block/unblock
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --block           should we block the user - default is unblock
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
```

## `gh_user_perms.py`
```
usage: gh_user_perms.py [-h] [--pat-key PATKEY] [--token TOKEN] [--no-archive] [--repo REPO] user org

Report on a user's permissions in an org.

positional arguments:
  user              Single user to examine in the org
  org               The org to examine

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --no-archive      Omit archived repos from the response
  --repo REPO       Single repo to examine in the org
```

## `org_audit_licensefile.py`
```
usage: org_audit_licensefile.py [-h] [--pat-key PATKEY] [--token TOKEN] [--archived] [--type {public,private,all}] [--include-URL]
                                [--orgini]
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
  --orgini              use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
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

## `org_owners.py`
```
usage: org_owners.py [-h] [--pat-key PATKEY] [--token TOKEN] [--orgini] [orgs ...]

Look at orgs, and get the list of owners

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
```

## `org_remove_user.py`
```
usage: org_remove_user.py [-h] [--pat-key PATKEY] [--token TOKEN] [--orgfile] [--do-it] username [orgs ...]

Given a username - go through all orgs in the orglist.ini file and see what they need to be removed from

positional arguments:
  username          User to remove
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --orgfile         use an ini file with the "orgs" entry with a csv list of all orgs to check, defaults to "orglist.ini"
  --do-it           Actually do the removal - Otherwise just report on what you found
```

## `org_repos.py`
```
usage: org_repos.py [-h] [--pat-key PATKEY] [--token TOKEN] [--without-org] [--archived] [--type {public,private,all}] org

Gets a list of Repos for an Org.

positional arguments:
  org                   The GH org to query

optional arguments:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --without-org         Include the org in the name, 'org/repo-name'
  --archived            Include archived repos. Default is unarchived only.
  --type {public,private,all}
                        Type of repo: private, public, all.
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
usage: repo_activity.py [-h] [--pat-key PATKEY] [--token TOKEN] [--issues] [--file FILE] [-i] [repos ...]

Gets a latest activity for a repo or list of repos. Also checks wiki for activity, and can be told to check for issues activity.

positional arguments:
  repos             list of repos to examine - or use --file for file base input

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --issues          Check the issues to set a date of activity if more recent than code
  --file FILE       File of 'owner/repo' names, 1 per line
  -i                Give visual output of that progress continues - useful for long runs redirected to a file
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

optional arguments:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --token TOKEN         use this PAT to access resources
  --perm PERM           String of the role name, defaults are 'read', 'write', 'triage', 'maintain', 'admin' - but others can be set
                        by the repo admin
  --org ORG             Organization/owner that the repos belong to
  --repos REPOS [REPOS ...]
                        list of repo names
  --apihost APIHOST     API host to connect to - default api.github.com
```

## `repo_archiver.py`
```
usage: repo_archiver.py [-h] [--pat-key PATKEY] [--token TOKEN] [--inactive] [--custom CUSTOM] [--file FILE] [--force] [--pause] [-q]
                        [repos ...]

Archive the specified repo, labelling and then closing out issues and PRs, per GitHub best practices. Closed issues/PRs, and
description/topic changes can be completely reversed using the repo_unarchiver script.

positional arguments:
  repos             owner/repo to archive

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --token TOKEN     use this PAT to access resources
  --inactive        Change the 'abandoned' and 'deprecated' wording to 'inactive'
  --custom CUSTOM   Custom text to add to issue/PR label, and description, less than 36 char long
  --file FILE       File with "owner/repo" one per line to archive
  --force           Don't stop if you detect previous archivers
  --pause           Pause upon detecting anomalies that might need fixing, but aren't blockers
  -q                DO NOT print, or request confirmations
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
# Supporting files

## `orglist.ini`
Used for scripts using lists of orgs, (currently only gh_file_search.py)
```
[GITHUB]
orgs = org1,org2,org3
```

## `.gh_pat.toml`
Used to store PAT files - used by several of the scripts.
Can be either in the repo directory or homedir.
Should be 600 permissions.
```
admin = "PAT1"
read-only = "PAT2"
key99 = "PAT99"

```

# GitHub-Scripts

A set of scripts for working with/analysis of github orgs/repos

## Requirements
[github3.py](https://github3py.readthedocs.io/en/master/index.html)

## Naming
Starts with:
* "gh_" - affects multiple orgs naturally.  (e.g. "How Much API rate is left")
* "org_" - limited to single orgs, occasionally multiple (e.g. "list all repos in ORG")
* "repo_" limited to just repos. (e.g. "Archive this repo")

## `gh_api_remain.py`
```
usage: gh_api_remain.py [-h] [--pat-key PATKEY]

Print out the remaining API limits, and the time of the reset

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
```

## `gh_file_search.py`
```
usage: gh_file_search.py [-h] --query QUERY [--orgini] [--pat-key PATKEY] [-v] [-f] [-t TIME] [orgs ...]

Get file search resuls for an org, returning repo list. e.g. if you want 'org:<ORGNAME> filename:<FILENAME> <CONTENTS>', then you
just need 'filename:<FILENAME> <CONTENTS>' and then list the orgs to apply it to. Note: There's a pause of ~10 seconds between org
searches due to GitHub rate limits - add a -v if you want notice printed that it's waiting

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --query QUERY     The query to run, without orgs
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  -v                Verbose - Print out that we're waiting for rate limit reasons
  -f                Print out file level responses rather than repo level
  -t TIME           Time to sleep between searches, in seconds, should be 10s or more
```

## `gh_org_licenses.py`
```
usage: gh_org_licenses.py [-h] [--pending] [--orgini] [--pat-key PATKEY] [orgs ...]

Provided a list of orgs, output how many GHE licenses are required.

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pending         Include Pending requests?
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
```

## gh_org_repo_perms.py
```
usage: gh_org_repo_perms.py [-h] [--pat-key PATKEY] [--user USER | --repo REPO] [-i] org

Depending on args, dump all repos in an org, repos for a user or users for a repo, and their user permissions, defaults to all repos
and users in an org.

positional arguments:
  org               The org to examine

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --user USER       Single user to examine in the org
  --repo REPO       Single repo to examine in the org
  -i                Give visual output of that progress continues - useful for long runs redirected to a file
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
usage: gh_user_moderation.py [-h] [--block] [--orgini] [--pat-key PATKEY] username [orgs ...]

Look at orgs, and either block or unblock the specified username

positional arguments:
  username          The GH user name to block/unblock
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --block           should we block the user - default is unblock
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
```

## `org_audit_licensefile.py`
```
usage: org_audit_licensefile.py [-h] [--archived] [--type {public,private,all}] [--orgini] [--pat-key PATKEY] orgs [orgs ...]

given the org, look through all repos of type, and archive status and report on github detected licenses.

positional arguments:
  orgs                  The org to work on

optional arguments:
  -h, --help            show this help message and exit
  --archived            Include archived repos. Default is unarchived only.
  --type {public,private,all}
                        Type of repo: private, public, all (Default).
  --orgini              use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
```

## `org_comms_team.py`
```
usage: org_comms_team.py [-h] [--team-name TEAM_NAME] [--pat-key PATKEY] [--users USERS [USERS ...]] [--remove] org

Go into an org, create a team named for the --team-name and add all members to it, OR if --users is specified - add that list of
users. Specify --remove to invert the operation

positional arguments:
  org                   organization to do this to

optional arguments:
  -h, --help            show this help message and exit
  --team-name TEAM_NAME
                        name of the team to create, defaults to 'everybody-temp-comms'
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --users USERS [USERS ...]
                        List of users to add to the team
  --remove              Remove the specified users from the team rather than add
```

## `org_repos.py`

```
usage: org_repos.py [-h] [--pat-key PATKEY] [--without-org] [--archived] [--type {public,private,all}] org

Gets a list of Repos for an Org.

positional arguments:
  org                   The GH org to query

optional arguments:
  -h, --help            show this help message and exit
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
  --without-org         Include the org in the name, 'org/repo-name'
  --archived            Include archived repos. Default is unarchived only.
  --type {public,private,all}
                        Type of repo: private, public, all.
```

## `org_secret_alerts.py`
```
usage: org_secret_alerts.py [-h] [--pat-key PATKEY] org

examine org for open security alerts from secret scanning, outputing csv data to pursue the alerts

positional arguments:
  org               The org that the repos are in

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
```

## `org_owners.py`
```
usage: org_owners.py [-h] [--orgini] [--pat-key PATKEY] [orgs ...]

Look at orgs, and get the list of owners

positional arguments:
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --orgini          use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
```

## `org_remove_user.py`
```
usage: org_remove_user.py [-h] [--pat-key PATKEY] [--orgfile] [--do-it] username [orgs ...]

Given a username - go through all orgs in the orglist.ini file and see what they need to be removed from

positional arguments:
  username          User to remove
  orgs              The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --orgfile         use an ini file with the "orgs" entry with a csv list of all orgs to check, defaults to "orglist.ini"
  --do-it           Actually do the removal - Otherwise just report on what you found
```

## `org_samlreport.py`
```
usage: org_samlreport.py [-h] [--url URL] [--pat-key PATKEY] [-f OUTPUT] org

Get SAML account mappings out of a GitHub org

positional arguments:
  org               The org to work on

optional arguments:
  -h, --help        show this help message and exit
  --url URL         the graphql URL
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  -f OUTPUT         File to store CSV to
```

## `org_teams.py`
```
usage: org_teams.py [-h] [--pat-key PATKEY] [--team TEAM] [--unmark] org

Gets a list of teams and their users for an Org. Users with '*' are maintainers of the team, reports using the team-slug

positional arguments:
  org               The GH org to query

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --team TEAM       The team slug to dump - if specified will ONLY use that team. (slug, NOT name)
  --unmark          Do not mark maintainers in the list
```

## `repo_activity.py`

```
usage: repo_activity.py [-h] [--pat-key PATKEY] [--issues] [--file FILE] [-i] [repos ...]

Gets a latest activity for a repo or list of repos. Also checks wiki for activity, and can be told to check for issues activity.

positional arguments:
  repos             list of repos to examine - or use --file for file base input

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --issues          Check the issues to set a date of activity if more recent than code
  --file FILE       File of 'owner/repo' names, 1 per line
  -i                Give visual output of that progress continues - useful for long runs redirected to a file
```

## `repo_add_perms.py`
```
usage: repo_add_perms.py [-h] --perm PERM --org ORG --repos REPOS [REPOS ...] [--apihost APIHOST] [--pat-key PATKEY]
                         {team,member} name

invite member or team to specified repos at specified level. If adding a user, if the user is a member, adds the member, else invites
as an OC.

positional arguments:
  {team,member}         team or member - specify type of perm
  name                  Name of the member or team to add

optional arguments:
  -h, --help            show this help message and exit
  --perm PERM           String of the role name, defaults are 'read', 'write', 'triage', 'maintain', 'admin' - but others can be set
                        by the repo admin
  --org ORG             Organization/owner that the repos belong to
  --repos REPOS [REPOS ...]
                        list of repo names
  --apihost APIHOST     API host to connect to - default api.github.com
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
```

## `repo_archiver.py`
```
usage: repo_archiver.py [-h] [--token TOKEN] [--pat-key PATKEY] [--inactive] [--custom CUSTOM] [--file FILE] [--force] [--pause] [-q]
                        [repos ...]

Archive the specified repo, labelling and then closing out issues and PRs, per GitHub best practices. Closed issues/PRs, and
description/topic changes can be completely reversed using the repo_unarchiver script.

positional arguments:
  repos             owner/repo to archive

optional arguments:
  -h, --help        show this help message and exit
  --token TOKEN     PAT to access github. Needs Write access to the repos
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  --inactive        Change the 'abandoned' and 'deprecated' wording to 'inactive'
  --custom CUSTOM   Custom text to add to issue/PR label, and description, less than 36 char long
  --file FILE       File with "owner/repo" one per line to archive
  --force           Don't stop if you detect previous archivers
  --pause           Pause upon detecting anomalies that might need fixing, but aren't blockers
  -q                DO NOT print, or request confirmations
```

## `repo_close_issues.py`
```
usage: repo_close_issues.py [-h] [--close-pr] [--comment COMMENT] [--doit] [--token TOKEN] [--pat-key PATKEY] [--delay DELAY]
                            org repo

Close issues associated with the specified repo. Do not close PRs unless specified, and only do things if specified

positional arguments:
  org                Org/owner name
  repo               Name of the repo

optional arguments:
  -h, --help         show this help message and exit
  --close-pr         Close the PRs too?
  --comment COMMENT  A comment to close the issue with
  --doit             Actually close things
  --token TOKEN      PAT to access github. Needs Write access to the repos
  --pat-key PATKEY   key in .gh_pat.toml of the PAT to use
  --delay DELAY      seconds between close requests, to avoid secondary rate limits > 1
```

## `repo_unarchiver.py`
```
usage: repo_unarchiver.py [-h] [--token TOKEN] [--pat-key PATKEY] [-q] repo

Reverse archival closing of issues of the specified repo, Note, repo MUST be manually unarchived before this script

positional arguments:
  repo              owner/repo to unarchive

optional arguments:
  -h, --help        show this help message and exit
  --token TOKEN     PAT to access github. Needs Write access to the repos
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use, default: 'admin'
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

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

## `org_comms_team.py`
```
usage: org_comms_team.py [-h] [--team-name TEAM_NAME] [--pat-key PATKEY] org

Go into an org, create a team named for the --team-name and add all members to it

positional arguments:
  org                   organization to do this to

optional arguments:
  -h, --help            show this help message and exit
  --team-name TEAM_NAME
                        name of the team to create, defaults to 'everybody-temp-comms'
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
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

## `org_user_membership.py`
```
usage: org_user_membership.py [-h] [--pat-key PATKEY] [-i] org

Gets a list of users for an org with how many repos they're involved with

positional arguments:
  org               The org to examine

optional arguments:
  -h, --help        show this help message and exit
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
  -i                Give visual output of that progress continues - useful for long runs redirected to a file
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

## `org_add_user.py`
```
usage: org_add_user.py [-h] [--repos REPOS [REPOS ...]] [--perms {read,write,admin}] [--pat-key PATKEY] username org

invite user to specified orgs at specified level

positional arguments:
  username              The GH user name add
  org                   The org that the repos are in

optional arguments:
  -h, --help            show this help message and exit
  --repos REPOS [REPOS ...]
                        The 'repo' to invite to
  --perms {read,write,admin}
                        permissions to add: read, write, admin.
  --pat-key PATKEY      key in .gh_pat.toml of the PAT to use
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

## `repo_archiver.py`
```
usage: repo_archiver.py [-h] [--token TOKEN] [--pat-key PATKEY] [--inactive] [--custom CUSTOM] [--file FILE] [--force] [-q]
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
  -q                DO NOT print, or request confirmations
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

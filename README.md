# GitHub-Scripts

A set of scripts for working with/analysis of github orgs/repos

## Requirements
[github3.py](https://github3py.readthedocs.io/en/master/index.html)

## org_repos.py 

```
usage: org_repos.py [-h] [--token TOKEN] [--without-org] [--archived] org

Gets a list of Repos for an Org.

positional arguments:
  org            The GH org to query

optional arguments:
  -h, --help     show this help message and exit
  --token TOKEN  GH token (PAT) with perms to examine your org
  --without-org  Include the org in the name, 'org/repo-name'
  --archived     Include archived repos. Default is unarchived only.
```

## repo_activity.py

```
usage: repo_activity.py [-h] [--token TOKEN] [--file FILE] [--parse-commit] [-i] [repos ...]

Gets a latest activity for a repo or list of repos

positional arguments:
  repos           list of repos to examine - or use --file for file base input

optional arguments:
  -h, --help      show this help message and exit
  --token TOKEN   github token with perms to examine your repo
  --file FILE     File of 'owner/repo' names, 1 per line
  --parse-commit  look at the weekly commits of the repo. Only useful if you care about usage in the last year.
  -i              Give visual output of that progress continues - useful for long runs redirected to a file
```

## `org_user_membership.py`
```
usage: org_user_membership.py [-h] [--token TOKEN] [--delay DELAY] [-i] org

Gets a list of users for an org with how many repos they're involved with

positional arguments:
  org            The org to examine

optional arguments:
  -h, --help     show this help message and exit
  --token TOKEN  The PAT to auth with
  --delay DELAY  delay between queries - rate limits, default to 1, should never hit the limit
  -i             Give visual output of that progress continues - useful for long runs redirected to a file
```

## `samlreport.py`
```
usage: samlreport.py [-h] [--url URL] [--token TOKEN] [-f OUTPUT] org

Get SAML account mappings out of a GitHub org

positional arguments:
  org            The org to work on

optional arguments:
  -h, --help     show this help message and exit
  --url URL      the graphql URL
  --token TOKEN  github token with perms to examine your org
  -f OUTPUT      File to store CSV to
```

## `repo_archiver.py`
```
usage: repo_archiver.py [-h] [--token TOKEN] [--pat-key PATKEY] [--file FILE] [--force] [-q] [repos ...]

Archive the specified repo, closing out issues and PRs

positional arguments:
  repos             owner/repo to archive

optional arguments:
  -h, --help        show this help message and exit
  --token TOKEN     PAT to access github. Needs Write access to the repos
  --pat-key PATKEY  key in .gh_pat.toml of the PAT to use
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

## `gh_gile_search.py`
```
usage: gh_file_search.py [-h] --query QUERY [--orgini] [--token TOKEN] [-v] [-t TIME] [orgs ...]

Get file search resuls for an org, returning repo list. e.g. if you want 'org:<ORGNAME> filename:<FILENAME> <CONTENTS>', then you just need 'filename:<FILENAME> <CONTENTS>' and then list the orgs to apply it to. Note: There's a pause of ~10 seconds between org searches due to GitHub rate limits - add a -v if you want notice printed that it's waiting

positional arguments:
  orgs           The org to work on

optional arguments:
  -h, --help     show this help message and exit
  --query QUERY  The query to run, without orgs
  --orgini       use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --token TOKEN  github token with perms to examine your org
  -v             Verbose - Print out that we're waiting for rate limit reasons
  -t TIME        Time to sleep between searches, in seconds, should be 10s or more
```

## `gh_user_moderation.py`
```
usage: gh_user_moderation.py [-h] [--block] [--orgini] [--token TOKEN] username [orgs ...]

Look at orgs, and either block or unblock the specified username

positional arguments:
  username       The GH user name to block/unblock
  orgs           The org to work on

optional arguments:
  -h, --help     show this help message and exit
  --block        should we block the user - default is unblock
  --orgini       use "orglist.ini" with the "orgs" entry with a csv list of all orgs to check
  --token TOKEN  github token with perms to examine your org
```

## `gh_comms_team.py`
```
usage: gh_comms_team.py [-h] [--team-name TEAM_NAME] [--token TOKEN] org

Go into an org, create a team named for the --team-name and add all members to it

positional arguments:
  org                   organization to do this to

optional arguments:
  -h, --help            show this help message and exit
  --team-name TEAM_NAME
                        name of the team to create, defaults to 'everybody-temp-comms'
  --token TOKEN         PAT to access github. Needs Write access to the repos
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

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
usage: repo_activity.py [-h] [--token TOKEN] [--delay DELAY] [--file FILE] [repos ...]

Gets a latest activity for a repo or list of repos

positional arguments:
  repos          list of repos to examine

optional arguments:
  -h, --help     show this help message and exit
  --token TOKEN  github token with perms to examine your repo
  --file FILE    File of org/repo names, 1 per line
  -i             Give visual output of that progress continues - useful for long runs redirected to a file  
```

## `org_user_mmbership.py`
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

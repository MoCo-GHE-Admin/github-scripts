# cis_tools

Tools for working with Mozilla's CIS/phonebook system and GitHub.

## Usage

```bash
# initial setup
# install poetry (https://python-poetry.org/)
poetry shell
poetry install

# every time
poetry shell

# populate database with all known CIS ids
./cis_db_tool.py enumerate_all_users
# get full details for all users with 'mozilla' in their primary email
./cis_db_tool.py get_details_mozilla

# get group email report (csv format)
./get_gh_org_emails.py mozilla-it
# get group email report with more info
./get_gh_org_emails.py mozilla-it -v

# query a single user
./cis_user_query.py -e mitchell@mozilla.com
# view raw CIS data for a userr
./cis_user_query.py -e mitchell@mozilla.com -r
# update the data we have for a user
./cis_user_query.py -e mitchell@mozilla.com -u
```

## Procuring Credentials

### CIS

See https://github.com/mozilla-iam/cis/blob/master/docs/PersonAPI.md#how-do-i-get-credentials-for-access for the steps to get a credential.

Your credential will need the following scopes (if you want LDAP groups and GHv4 IDs in results).

```bash
classification:public
classification:workgroup
classification:workgroup:staff_only
display:none
display:public
display:authenticated
display:vouched
display:staff
display:all
```

mildly confusing example bugzilla ticket: https://bugzilla.mozilla.org/show_bug.cgi?id=1719486

Enter the credentials in `.cis_oauth.toml`

```bash

client_id = "YOUR_SECRET"
client_secret = "LONGER_SECRET"
```

### GH

- Go to https://github.com/settings/tokens (Settings > Developer settings).
- Create a new token with the following abilities:
  - public_repo, read:org, read:user, repo:status, repo_deployment

Enter the credentials in `.gh_pat.toml`.

```bash
read_only = "KEY_GOES_HERE"
```

## Alternative methods for getting GH group email data

### Scanning DynamoDB

It's possible to get this data directly from Dynamo DB (the backing store for CIS). It's much faster (like 2 minutes).

rtucker has access and says it works. His query:

```bash
# in production-identity-vault dynamodb (not sure which AWS account)
 "id, primary_email, flat_profile.username, flat_profile.primary_username, flat_profile.identities.github_id_v4"
```

## TODO

- rename Moz_GHE_Tools? GHE_Tools?
  - GH_admin_tools... not necessarily for GHE

## Answered Questions

- Can we eliminate need to enumerate and decorate via CIS API?
  - use dinopark v4 api?
    - https://people.mozilla.org/api/v4/search/simple/?q=sciurus&w=staff
      - not possible.
        - api key not available.
        - could return multiple results per search term (can't search just gh_v4_id field).

## debugging

####finding users who have multiple CIS accounts with same GH token

```sql
select  * from user where gh_v4_id  in (select gh_v4_id from user group  by gh_v4_id  having count(*) > 1) order by gh_v4_id;
```

Why would they have multiple?
- External contributors who are now employees?


##  links

- CIS
  - https://github.com/mozilla-iam/cis
    - https://github.com/mozilla-iam/cis/blob/master/docs/PersonAPI.md
- Peewee ORM
  - http://docs.peewee-orm.com/en/latest/
- Tool to convert curl to python
  - https://curl.trillworks.com/
- Github3.py
  - https://github3.readthedocs.io
- Github API
  - https://docs.github.com/en/rest/reference/users

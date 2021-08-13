#!/usr/bin/env python3

import peewee
from cis import db
from peeweext.fields import DatetimeTZField
from playhouse.migrate import *

migrator = SqliteMigrator(db)

# investigating database
#
# sqlite3 cis.db
# .tables
# .schema user

# only un-comment if your db is missing the fields (they're not re-entrant/can't be rerun once already done)
# migrate(migrator.add_column("user", "last_updated", DatetimeTZField(null=True)))
# migrate(migrator.add_column("user", "mozilla_ldap_primary_email", peewee.CharField(null=True)))

# dump-snowflake
Dump the structure of one or all Snowflake databases to the filesystem

## Quick Guide

(either inside a venv or globally)

* `pip install git+https://github.com/global-data-team/dump-snowflake.git@databases`
* Set environment variables `DBT_PROFILES_USER` and `DBT_PROFILES_PASSWORD` to your
  Snowflake username & password respectively. NB unless you override it (cf below),
  your account must have accountadmin privilege
* `dump_snowflake_databases` <name of database>

   This will create a local folder called <name of database> containing a folder
   for each object type in the database, eg:

```
dump_snowflake_databases TJG

+---database
¦       TJG.sql
¦
+---schema
¦       TJG.PUBLIC.sql
¦       TJG.TEST.sql
¦       TJG.XXX.sql
¦
+---table
¦       TJG.TEST.PERMISSIONS .sql
¦       TJG.TEST.T1 .sql
¦       TJG.TEST.T2 .sql
¦       TJG.TEST.T3 .sql
¦       TJG.XXX.YYY .sql
¦
+---view
        TJG.PUBLIC.V_YYY.sql
```

## Entire Database

**_NB this mode removes all folders in the current directory; make sure you're in a
suitable directory before running it_**

Run `dump_snowflake_databases`

This will create a folder for every database in the Snowflake instance

## Command-line switches

**Quick version:** Run `dump_snowflake_databases --help`

### Useful options

* The only positional parameter is a SQL-wildcard pattern; only databases
  matching that pattern, eg:

  `dump_snowflake_databases DS_EXTERION_DWH`

* `--snowflake_role` - if your user doesn't have the `accountadmin` role, specify
  a role which has access to the databases you're writing out.

## Notes

This was developed and tested on Windows. It should run without changes on other OS
but let me know if it doesn't!

In particular, if you're on Windows you might need to enable Git's support for long
filenames:

`git config --system core.longpaths true`


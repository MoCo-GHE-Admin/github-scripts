#!/usr/bin/env python3

import sys
import traceback

import click
import pendulum
from cis_tools import cis

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


# TODO: refactor this away and just pass a CIS object?
#  it does do a db_connect, but CIS could also...?
class CisTool:
    def __init__(self):
        self.cis_instance = cis.CIS()
        # connect to db
        self.cis_instance.db_connect()


pass_class = click.make_pass_decorator(CisTool)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    ctx.obj = CisTool()


@cli.command()
@pass_class
def enumerate_all_users(ct_instance):
    ct_instance.cis_instance.create_users_from_users_id_all_query()


# TODO: this might still be useful...
#  If the user wants to get a full dump as fast as possible this is probably the best once
#  it's reworked to use the blob data it gets (I didn't think it got it, so it doesn't use it).
def enumerate_all_users_old(ct_instance):
    click.echo("enumerating all CIS users...")
    # TODO: show elapsed time
    before = ct_instance.cis_instance.db_get_users()
    try:
        ct_instance.cis_instance.create_users_from_users_query()
    except Exception as e:
        print("*** error encountered")
        # print the full stack trace of the exception
        traceback.print_exception(*sys.exc_info())
    after = ct_instance.cis_instance.db_get_users()
    print("users: before: %s, after: %s" % (before, after))


@cli.command()
@pass_class
def get_details_mozilla(ct_instance):
    start_time = pendulum.now()
    click.echo("getting full details for likely-mozilla users...")
    ct_instance.cis_instance.decorate_mozilla_users(force_update=False)
    end_time = pendulum.now()
    print("-------")
    print("elapsed time: %s" % end_time.diff_for_humans(start_time, True))


@cli.command()
@pass_class
def get_details_all(ct_instance):
    start_time = pendulum.now()
    click.echo("getting full details for all users...")
    ct_instance.cis_instance.decorate_users()
    end_time = pendulum.now()
    print("-------")
    print("elapsed time: %s" % end_time.diff_for_humans(start_time, True))


if __name__ == "__main__":
    cli()

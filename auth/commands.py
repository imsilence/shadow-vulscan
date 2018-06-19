#encoding: utf-8

import traceback

import click

from flask.cli import AppGroup

from shadow import app


from .models import User

cli = AppGroup('auth')


@cli.command('create-user')
@click.option('--name', type=str, prompt=True, help='name')
@click.option('--email', type=str, prompt=True, help='email')
@click.option('--is_super', type=bool, is_flag=True, help='is super man')
@click.option('--password', type=str, prompt=True, hide_input=True, confirmation_prompt=True, help="password")
def create_user(name, email, is_super, password):
    try:
        user, has_error, errors = User.create(name=name, email=email, is_super=is_super, password=password)
        if has_error:
            click.echo('fail create user:')
            for key, error in errors.items():
                click.echo(error.msg)
        else:
            click.echo("success create user")
    except BaseException as e:
        click.echo("fail create user, reason:{0}".format(e))
        app.logger.exception(e)
        app.logger.error(traceback.format_exc())

app.cli.add_command(cli)

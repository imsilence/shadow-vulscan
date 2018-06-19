#encoding: utf-8

import click

from flask.cli import AppGroup

from . import app
from . import db

cli = AppGroup('shadow')

@cli.command('init-db')
def init_db():
    db.create_all()
    click.echo('success init db')


app.cli.add_command(cli)
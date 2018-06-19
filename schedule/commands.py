#encoding: utf-8

import threading
import logging
import traceback
import os
import time
import socket


import click
from flask.cli import AppGroup

from shadow import app

from .models import JobType



cli = AppGroup('schedule')

logger = logging.getLogger(__name__)


@cli.command('start-schedule')
def schedule():
    logger.info('schedule process is starting...')
    logger.info('pid:%s', os.getpid())

    from .dispatcher import preprocess, dispatch, result

    funcs = [preprocess, dispatch, result]

    for func in funcs:
        th = threading.Thread(target=func)
        th.daemon = True
        th.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt as e:
        pass
    except BaseException as e:
        logger.exception(e)
        logger.error(traceback.format_exc())



@cli.command('start-execute')
@click.option('--protocol', type=str, default='http', help='protocol')
@click.option('--host', type=str, default='localhost', help='host')
@click.option('--port', type=int, default=5000, help='port')
@click.option('--type', type=click.Choice(list(map(str, JobType.KEYS.keys()))), default='2', help='type')
@click.option('--concurrent', type=int, default=1, help='concurrent')
@click.option('--ident', type=str, default=socket.gethostname(), help='ident')
@click.option('--hostname', type=str, default=socket.gethostname(), help='hostname')
def execute(**kwargs):
    logger.info('execute process is straing...')
    logger.info('pid:%s', os.getpid())
    kwargs['pid'] = os.getpid()

    from .executor import heartbeat, handle

    funcs = [heartbeat, handle]

    for func in funcs:
        th = threading.Thread(target=func, kwargs=kwargs)
        th.daemon = True
        th.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt as e:
        pass
    except BaseException as e:
        logger.exception(e)
        logger.error(traceback.format_exc())


app.cli.add_command(cli)


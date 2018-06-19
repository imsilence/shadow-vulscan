#encoding: utf-8

import logging
import traceback

from redis import StrictRedis

logger = logging.getLogger(__name__)

class RedisCli(object):
    def __init__(self, app=None):
        self.conn = None
        self.app = app

    def init_app(self, app):
        self.app = app

    def reconnect(self):
        try:
            if self.app is None:
                raise BaseException('flask app not initialize')
            self.conn = StrictRedis(**self.app.config.get('REDIS'))
            self.ping()
        except BaseException as e:
            logger.exception(e)
            logger.error(traceback.format_exc())
            self.conn = None

    def __getattr__(self, key):
        if self.conn is None:
            self.reconnect()

        if self.conn:
            return getattr(self.conn, key, None)

        return None
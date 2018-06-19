#encoding: utf-8
import logging


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import AppConfig, REDIS_KEYS, DEFAULT_CONCURRENT

app = Flask(__name__)

app.config.from_object(AppConfig)


logging.basicConfig(
    level=logging.DEBUG if app.config.get('DEBUG', 0) else logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

db = SQLAlchemy(app)

from utils.rediscli import RedisCli


redis = RedisCli(app)

from . import views
from . import commands

import auth
import dashboard
import schedule
import asset
import vul

app.register_blueprint(auth.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(schedule.bp)
app.register_blueprint(asset.bp)
app.register_blueprint(vul.bp)
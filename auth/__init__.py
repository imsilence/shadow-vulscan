#encoding: utf-8

from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth', static_folder='static', template_folder='templates')

from . import views
from . import models

from . import hooks

from . import commands
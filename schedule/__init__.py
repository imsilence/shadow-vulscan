#encoding: utf-8

from flask import Blueprint

bp = Blueprint('schedule', __name__, url_prefix='/schedule', static_folder='static', template_folder='templates')

from . import views
from . import models
from . import commands
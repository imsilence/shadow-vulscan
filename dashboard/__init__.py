#encoding: utf-8

from flask import Blueprint

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard', static_folder='static', template_folder='templates')

from . import views
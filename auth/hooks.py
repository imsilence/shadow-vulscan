#encoding: utf-8

from flask import session, g

from . import bp

from .models import User


@bp.before_app_request
def load_user():
    g.user = None
    if session.get('user'):
        g.user = User.get_by_key(session.get('user'))
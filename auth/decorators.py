#encoding: utf-8

from functools import wraps

from flask import request, g, redirect, url_for

from shadow import response

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.user is None:
            return response.json(response.STATUS_UNAUTHENTICATE) if request.is_xhr else redirect(url_for('auth.login', next=request.path))

        rt = func(*args, **kwargs)
        return rt

    return wrapper


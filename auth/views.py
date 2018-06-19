#encoding: utf-8

from flask import session, request, render_template, url_for, redirect, g

from shadow import response

from . import bp

from .decorators import login_required

from .models import Role, User


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login/', methods=['POST'])
def login(next=None):
    if g.user:
        return response.json(result={'next' : request.args.get('next') or '/'}) if request.is_xhr else redirect('/')

    name, password, errors = '', '', {}
    if request.method == 'POST':
        name = request.form.get('name', '')
        password = request.form.get('password', '')
        user = User.authenticate(name, password)
        if user:
            session['user'] = user.id
            return response.json(result={'next' : request.args.get('next') or '/'})
        else:
            errors['user'] = '用户名或密码错误'
            return response.json(errors=errors)
    return render_template('auth/login.html', name=name, password=password, errors=errors)


@bp.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/users/')
@login_required
def users():
    return render_template('auth/user.html', users=User.all())

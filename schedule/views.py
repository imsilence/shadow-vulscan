#encoding: utf-8

import time

from flask import request, render_template

from shadow.response import json
from . import bp
from .models import Executor
from auth.decorators import login_required

@bp.route('/register/', methods=['POST'])
def register():
    ident = request.json.get('ident', '')
    hostname = request.json.get('hostname', '')
    pid = request.json.get('pid', '')
    type = request.json.get('type', '')
    total = request.json.get('total', 0)
    busy = request.json.get('busy', 0)
    idle = request.json.get('idle', 0)

    Executor.create(ident=ident, hostname=hostname, pid=pid, type=type, total=total, busy=busy, idle=idle)
    return json(result={'time' : time.time()})

@bp.route('/executors/')
@login_required
def executors():
    return render_template('schedule/executor.html', executors=Executor.all(False))

@bp.route('/executors/', methods=['POST'])
@login_required
def delete_executor():
    Executor.delete_by_key(request.form.get('id', 0))
    return json()
#encoding: utf-8

from flask import render_template
from auth.decorators import login_required

from shadow.response import json

from . import bp
from .models import SysAsset

@bp.route('/')
@bp.route('/sys_asset/')
@login_required
def sys_asset():
    return render_template('asset/sys_asset.html', assets=SysAsset.all())


@bp.route('/sys_asset/list/')
@login_required
def list_sys_asset():
    assets=[asset.as_dict() for asset in SysAsset.all()]
    return json(assets)


@bp.route('/sys_asset/delete/')
@login_required
def delete_sys_asset():
    SysAsset.delete_by_key(request.form.get('id', 0))
    return json()
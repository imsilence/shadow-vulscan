#encoding: utf-8

from flask import render_template, request, g

from . import bp

from shadow.response import json, STATUS_PARAMS_ERROR
from auth.decorators import login_required

from .models import SysVulJob, SysVulPlugin, PluginConfig, AssetSysVul

@bp.route('/')
@bp.route('/sys_vul_job/')
@login_required
def sys_vul_job():
    plugins = SysVulPlugin.all()
    return render_template('vul/sys_vul_job.html', plugins=plugins)


@bp.route('/sys_vul/job/list/')
@login_required
def list_sys_vul_job():
    jobs = [job.as_dict() for job in SysVulJob.all()]
    return json(result=jobs)


@bp.route('/sys_vul/job/create/', methods=['POST'])
@login_required
def create_sys_vul_job():
    name = request.form.get('name')
    ip = request.form.get('ip')
    concurrent_discover = request.form.get('concurrent_discover')
    concurrent_check = request.form.get('concurrent_check')
    plugins = request.form.getlist('plugins')

    SysVulJob.create(g.user, name, ip, concurrent_discover, concurrent_check, plugins)
    return json(result=[])


@bp.route('/sys_vul/job/report/', methods=['POST'])
@login_required
def report_sys_vul_job():
    job = SysVulJob.get_by_key(request.form.get('id', 0))
    if job:
        return json(result=job.as_dict())
    else:
        return json(code=STATUS_PARAMS_ERROR)


@bp.route('/sys_vul/job/cancel/', methods=['POST'])
@login_required
def cancel_sys_vul_job():
    SysVulJob.cancel(request.form.get('id', 0))
    return json(result=[])


@bp.route('/sys_vul/job/delete/', methods=['POST'])
@login_required
def delete_sys_vul_job():
    SysVulJob.delete(request.form.get('id', 0))
    return json(result=[])


@bp.route('/sys_vul/plugin/')
@login_required
def sys_vul_plugin():
    return render_template('vul/sys_vul_plugin.html')


@bp.route('/sys_vul/plugin/list/')
@login_required
def list_sys_vul_plugin():
    plugins = [plugin.as_dict() for plugin in SysVulPlugin.all()]
    return json(result=plugins)


@bp.route('/sys_vul/plugin/report/', methods=['POST'])
@login_required
def report_sys_vul_plugin():
    plugin = SysVulPlugin.get_by_key(request.form.get('id', 0))
    if plugin:
        return json(result=plugin.as_dict())
    else:
        return json(code=STATUS_PARAMS_ERROR)


@bp.route('/sys_vul/plugin/save/', methods=['POST'])
@login_required
def save_sys_vul_plugin():
    params = {k : v for k, v in request.form.items()}
    obj, has_error, errors = SysVulPlugin.create_or_replace(**params)
    if has_error:
        return json(code=STATUS_PARAMS_ERROR, errors=errors)
    return json(result=[])


@bp.route('/sys_vul/plugin/delete/', methods=['POST'])
@login_required
def delete_sys_vul_plugin():
    SysVulPlugin.delete(request.form.get('id', 0))
    return json(result=[])


@bp.route('/plugin_config/')
@login_required
def plugin_config():
    return render_template('vul/plugin_config.html')


@bp.route('/plugin_config/list/')
@login_required
def list_plugin_config():
    configs = [config.as_dict() for config in PluginConfig.all()]
    return json(result=configs)


@bp.route('/sys_vul/plugin_config/report/', methods=['POST'])
@login_required
def report_plugin_config():
    config = PluginConfig.get_by_key(request.form.get('id', 0))
    if config:
        return json(result=config.as_dict())
    else:
        return json(code=STATUS_PARAMS_ERROR)


@bp.route('/sys_vul/plugin_config/save/', methods=['POST'])
@login_required
def save_plugin_config():
    params = {k : v for k, v in request.form.items()}
    obj, has_error, errors = PluginConfig.create_or_replace(**params)
    if has_error:
        return json(code=STATUS_PARAMS_ERROR, errors=errors)
    return json(result=[])


@bp.route('/sys_vul/plugin_config/delete/', methods=['POST'])
@login_required
def delete_plugin_config():
    PluginConfig.delete(request.form.get('id', 0))
    return json(result=[])


@bp.route('/sys_vul/report_sys_vul/list/', methods=['POST'])
@login_required
def list_report_sys_vul():
    vuls = AssetSysVul.all(request.form.get('key', ''))
    vuls = [vul.as_dict() for vul in vuls]
    return json(result=vuls)


@bp.route('/sys_vul/')
@login_required
def sys_vul():
    return render_template('vul/sys_vul.html', vuls=AssetSysVul.all())
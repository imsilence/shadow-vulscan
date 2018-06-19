#encoding: utf-8

from flask import render_template

from shadow.response import json

from . import bp

from auth.decorators import login_required

from asset.models import SysAsset, Application
from vul.models import AssetSysVul
from schedule.models import Executor



@bp.route('/')
@login_required
def index():
    #最新发现资产数量/总资产数量/存在漏洞的主机数量
    #最新发现端口数量/总端口数量
    #最新发现漏洞数量/总漏洞数量
    #端口统计
    #漏洞发现主机统计
    #主机发现漏洞统计

    stats = {}
    stats['asset'] = SysAsset.stats()
    stats['app'] = Application.stats()
    stats['vul'] = AssetSysVul.stats()
    stats['executor'] = Executor.stats()
    stats['stats_port'] = Application.stats_port()
    stats['stats_host_vul'] = AssetSysVul.stats_host_vul()
    stats['stats_vul_host'] = AssetSysVul.stats_vul_host()
    return render_template('dashboard/index.html', stats=stats)



@bp.route('/stats/')
@login_required
def stats():
    #最新发现资产数量/总资产数量/存在漏洞的主机数量
    #最新发现端口数量/总端口数量
    #最新发现漏洞数量/总漏洞数量
    #端口统计
    #漏洞发现主机统计
    #主机发现漏洞统计
    stats = {}
    stats['asset'] = SysAsset.stats()
    stats['app'] = Application.stats()
    stats['vul'] = AssetSysVul.stats()
    stats['executor'] = Executor.stats()
    stats['stats_port'] = Application.stats_port()
    stats['stats_host_vul'] = AssetSysVul.stats_host_vul()
    stats['stats_vul_host'] = AssetSysVul.stats_vul_host()
    return json(stats)
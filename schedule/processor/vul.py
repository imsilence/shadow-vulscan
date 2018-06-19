#encoding: utf-8

import logging
import traceback

from shadow import REDIS_KEYS, DEFAULT_CONCURRENT

from .base import Processor

from ..models import Job, SubJob, JobType, SubJobResult
from asset.models import SysAsset
from vul.models import AssetSysVul

from utils.iputils import IPUtils
from utils import timezone

logger = logging.getLogger(__name__)

class SysVulScanProcessor(Processor):

    def preprocess(self, job):
        #先进行资产发现，再进行漏洞扫描
        logger.debug('preprocess job: %s', job)
        ip = job.job_params_object.get('ip', '')
        concurrent = int(job.job_params_object.get('concurrent', {}).get('discover', DEFAULT_CONCURRENT))
        splits = IPUtils.split_ip_ranges(ip, concurrent * 2)

        logger.debug('subjob ip nodes: %s', splits)

        for split in splits:
            if len(split) == 0:
                continue
            job_params = {
                'ip' : list(map(lambda x: list(map(str, x)), split))
            }
            sub_job = SubJob.create(job, JobType.SYS_ASSET_DISCOVER, job_params)
            logger.debug('create sub job: %s', sub_job)


    def get_job_queue_keys(self, job):
        return {
            'discover' : REDIS_KEYS['JOB_QUEUE'].format(type=JobType.KEYS[JobType.SYS_ASSET_DISCOVER], id=job.id),
            'check' : REDIS_KEYS['JOB_QUEUE'].format(type=JobType.KEYS[JobType.SYS_VUL_CHECK], id=job.id)
        }


    def result(self, sub_job, type, result):
        data = result.get('data', [])

        if sub_job.type == JobType.SYS_ASSET_DISCOVER:
            job = sub_job.job
            for asset in data:
                # 存储资产
                obj = SysAsset.create_or_replace(**asset)
                job_params = {
                    'ip' : obj.ip,
                    'plugins' : job.job_params_object.get('plugins', []),
                }
                # 下载漏洞检查任务
                SubJob.create(job, JobType.SYS_VUL_CHECK, job_params)
        elif sub_job.type == JobType.SYS_VUL_CHECK:
            now = timezone.now()
            for asset in data:
                key = asset.get('key', '')
                for k, v in asset.items():
                    if k == 'key':
                        continue
                    AssetSysVul.create_or_replace(key=key, plugin_ident=k, payloads=v.get('payloads', {}))

                AssetSysVul.delete_not_found(key, now)

        sub_job.finish(status=result.get('status'), explain=result.get('explain', ''))
        SubJobResult.create(sub_job,data)

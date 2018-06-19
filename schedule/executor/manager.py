#encoding: utf-8

import logging
import traceback
import os
import time
from queue import Queue, Empty, Full
import json
import threading
import importlib

import requests

from shadow import redis, REDIS_KEYS

from ..models import SubJob, JobType

logger = logging.getLogger(__name__)

class ExecutorManager(object):

    def __init__(self, concurrent, *args, **kwargs):
        self.concurrent = concurrent
        self.works = {}
        self.jobs = Queue(concurrent)
        self.results = Queue()


    def start(self):
        self._init_works()
        self._init_result()


    def get_executor(self, type):
        name = JobType.KEYS.get(int(type), None)
        if name is None:
            return None
        try:
            mod = importlib.import_module('schedule.executor.{0}'.format(name))
            clazz = getattr(mod, 'Executor', None)
            return clazz(name)
        except ImportError as e:
            logger.exception(e)
            logger.error(traceback.format_exc())
            return None


    def _init_works(self):
        for _ in range(self.concurrent):
            th = threading.Thread(target=self.execute, kwargs={'jobs' : self.jobs, 'results' : self.results})
            th.daemon = True
            self.works[th.ident] = th
            th.start()
            logger.info('work threading is starting...')
            logger.info('threading ident: %s', th.ident)


    def _init_result(self):
        th = threading.Thread(target=self.do_result)
        th.daemon = True
        th.start()
        logger.info('result threading is straring...')


    def do_result(self):
        result = None
        while True:
            try:
                result = self.results.get(block=True, timeout=3)
            except Empty as e:
                continue

            logger.info('threading do result: %s', result)
            try:
                redis.lpush(REDIS_KEYS['JOB_RESULT'], json.dumps(result))
            except BaseException as e:
                logger.error('do result failure, result: %s', result)
                logger.exception(e)
                logger.error(traceback.format_exc())


    def do(self, job):
        try:
            self.jobs.put(job, block=True, timeout=3)
            return True
        except Full as e:
            return False


    def execute(self, jobs, results):
        job = None
        while True:
            try:
                job = jobs.get(block=True, timeout=3)
            except Empty as e:
                continue

            logger.info('threading execute job: %s', job)

            result = {'status' : SubJob.STATUS_SUCCESS, 'data' : None}
            try:
                job = json.loads(job)
                executor = self.get_executor(int(job.get('type')))
                if executor:
                    executor.init(job)
                    result['data'] = executor.run(job)
                    executor.destory()
                else:
                    result = {
                        'status' : SubJob.STATUS_FAILURE,
                        'explain' : 'executor not found'
                    }
            except BaseException as e:
                logger.error('execute job failure: %s', job)
                logger.exception(e)
                logger.error(traceback.format_exc())
                result = {'status' : SubJob.STATUS_FAILURE, 'explain' : str(e)}

            logger.info('job execute finish, job: %s, result: %s', job, result)
            results.put({'id' : job.get('id'), 'type' : 'over', 'result' : result})


def heartbeat(protocol, host, port, type, concurrent, ident, hostname, pid, *args, **kargs):
    logger.info('heartbeat threading is starting...')
    url = '{protocol}://{host}:{port}/schedule/register/'.format(protocol=protocol, host=host, port=port)
    while True:
        try:
            register = {
                'ident' : ident,
                'type' : type,
                'hostname' : hostname,
                'pid' : pid,
                'total' : concurrent,
                'busy' : 0,
                'idle' : concurrent - 0,
            }
            logger.debug('register: %s', register)
            response = requests.post(url, json=register)

            if not response.ok:
                logger.error('heartbeat failure, code: %s, reason: %s', response.status_code, response.reason)
            else:
                logger.debug('heartbeat success, response: %s', response.text)
        except BaseException as e:
            logger.exception(e)
            logger.error(traceback.format_exc())

        time.sleep(30)


def handle(type, concurrent, ident, hostname, pid, *args, **kwargs):
    logger.info('handle threading is starting...')

    executor = ExecutorManager(concurrent=concurrent)
    executor.start()

    queue = REDIS_KEYS['JOB_EXECUTOR'].format(type=type, ident=ident)
    while True:
        job = redis.brpop(queue, timeout=3)
        if job is None:
            continue
        job = job[1]
        logger.info('handle job: %s', job)
        if not executor.do(job):
            logger.info('job queue is full, job go back:%s', job)
            redis.rpush(queue, job)

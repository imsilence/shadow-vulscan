#encoding: utf-8

import logging
import traceback
import threading
import time
import json

from shadow import DEFAULT_CONCURRENT, redis, REDIS_KEYS

from ..models import Executor, SubJob, Job, JobType
from ..processor.manager import Manager as ProcessorManager


logger = logging.getLogger(__name__)


class ExecutorManager(object):

    def __init__(self, *args, **kwargs):
        self.executors = {}
        self.lock = threading.Lock()
        th = threading.Thread(target=self.load_executors)
        th.daemon = True
        th.start()


    def load_executors(self):
        while True:
            executors = {}
            for executor in Executor.all():
                executors.setdefault(executor.type, [])
                executors[executor.type].append(executor)

            logger.info('current executors: %s', executors)

            with self.lock:
                self.executors = executors

            time.sleep(60)


    def dispatch(self, sub_job):
        logger.debug('dispatch job: %s', sub_job)

        executors = []

        with self.lock:
            executors = self.executors.get(sub_job.type, [])

        logger.info('current executors: %s', [x.as_dict() for x in executors])
        available = lambda x : int(x.total) > x.inuse
        key = lambda x : (x.total - x.inuse) / x.total
        executors = sorted(filter(available, executors), key=key, reverse=True)
        if executors:
            logger.info('dispatch job to executor, job:%s, executor:%s', sub_job, executors[0])
            return executors[0].execute(sub_job)

        return False



class DispatcherManager(object):

    def __init__(self):
        self.processorManager = ProcessorManager()
        self.executorManager = ExecutorManager()

    def preprocess(self, job):
        processor = self.processorManager.get(job.type)
        if processor is None:
            logger.info('processor not found, job preprocess failure, job: %s', job)
            job.finish(job.STATUS_FAILURE)
            return False

        processor.preprocess(job)
        job.preprocess()
        return True


    def dispatch(self, job):
        processor = self.processorManager.get(job.type)
        if processor is None:
            logger.info('processor not found, job dispatch failure, job: %s', job)
            job.finish(job.STATUS_FAILURE)
            return False

        keys = processor.get_job_queue_keys(job)
        concurrents = job.job_params_object.get('concurrent', {})

        for name, key in keys.items():
            limit = concurrents.get(name, DEFAULT_CONCURRENT)
            infos = redis.zrange(key, 0, int(limit) - 1, withscores=True)

            for sub_job_id, score in infos:
                if int(score) != 0:
                    continue

                sub_job = SubJob.get_by_key(sub_job_id)
                if sub_job is None:
                    continue

                if not self.executorManager.dispatch(sub_job):
                    logger.info('dispatch sub job failure, Out of executor idel num, job: %s', sub_job)
                    break

        return True

    def result(self, sub_job, type, result):
        processor = self.processorManager.get(sub_job.job.type)
        if processor is None:
            logger.info('processor not found, result dispose failure, sub_job: %s, result: %s', sub_job, result)
            return False

        processor.result(sub_job, type, result)
        processor.progress(sub_job.job)
        return True



def preprocess():
    logger.info('preprocess threading is starting...')
    dispatcher = DispatcherManager()
    while True:
        job_id = redis.brpop(REDIS_KEYS['JOB_PREPROCESS'], timeout=3)
        if job_id is None:
            continue

        job_id = job_id[1]
        logger.debug('preprocess job id: %s', job_id)

        job = Job.get_by_cache(job_id)
        if job is None:
            logger.info('job not found, id: %s', job_id)
            continue

        dispatcher.preprocess(job)


def dispatch():
    logger.info('dispatch threading is string...')
    dispatcher = DispatcherManager()
    while True:
        job_id = redis.brpop(REDIS_KEYS['JOB_DOING'], timeout=3)
        if job_id is None:
            continue
        job_id = job_id[1]

        logger.debug('dispatch job id: %s', job_id)
        job = Job.get_by_cache(job_id)
        if job is None:
            logger.info('job not found, id: %s', job_id)
            continue

        redis.lpush(REDIS_KEYS['JOB_DOING'], job_id)
        dispatcher.dispatch(job)
        time.sleep(3)


def result():
    logger.info('result threading is string...')
    dispatcher = DispatcherManager()
    while True:
        result = redis.brpop(REDIS_KEYS['JOB_RESULT'], timeout=3)
        if result is None:
            continue

        result = result[1]
        logger.debug('dispose result: %s', result)
        try:
            result = json.loads(result)
            sub_job = SubJob.get_by_key(result.get('id'))
            if sub_job is None:
                logger.info('sub job not found: %s', result)
                continue
            dispatcher.result(sub_job, result.get('type'), result.get('result'))
        except BaseException as e:
            logger.error('dispose result failure: %s', result)
            logger.exception(e)
            logger.error(traceback.format_exc())

#encoding: utf-8

import logging
from functools import reduce

from shadow import redis

logger = logging.getLogger(__name__)

class Processor(object):

    def preprocess(self, job):
        raise BaseException('override method preprocess')

    def result(self, sub_job, type, result):
        raise BaseException('override method result')

    def get_job_queue_keys(self, job):
        return {}

    def progress(self, job):
        keys = self.get_job_queue_keys(job)
        flags = []
        rates = []
        totals = []
        ones = []
        for name, key in keys.items():
            total = redis.zcard(key)
            one = redis.zcount(key, 1, 1)
            totals.append(total)
            ones.append(one)
            flags.append(False if total == 0 else one == total)
            rates.append(0 if total == 0 else (one / total))


        rates_nozero = list(filter(lambda x: x > 0.001 , rates))
        if rates_nozero:
            job.doing(int(1 - rates.count(0)/len(rates)) * reduce(lambda x, y: x * y, rates_nozero) * 100)

        if all(flags) or (totals[0] == ones[0] and totals[1] == 0):
            logger.info('job finish: %s', job)
            job.finish()
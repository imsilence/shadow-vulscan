#encoding: utf-8

from datetime import timedelta
import json

from flask import g

from shadow import db, redis, REDIS_KEYS
from shadow.models import AsDictMixin
from utils import timezone

from auth.models import User

import logging

logger = logging.getLogger(__name__)

class JobType(object):
    SYS_VULSCAN = 1
    SYS_ASSET_DISCOVER = 2
    SYS_VUL_CHECK = 3
    WEB_VULSCAN = 4
    WEB_ASSET_DISCOVER = 5
    WEB_VUL_CHECK = 6

    KEYS = {
        1 : 'sys_vulscan',
        2 : 'sys_asset_discover',
        3 : 'sys_vul_check',
        4 : 'web_vulscan',
        5 : 'web_asset_discover',
        6 : 'web_vul_check',
    }


class Job(db.Model, AsDictMixin):

    STATUS_WATING = 1
    STATUS_PREPROCESS = 2
    STATUS_DOING = 3
    STATUS_CANCEL = 4
    STATUS_SUCCESS = 5
    STATUS_FAILURE = 6
    STATUS_DELETE = 7

    PROGRESS_PREPROCESS = 0
    PROGRESS_DOING = 5
    PROGRESS_COMPLATE = 100

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False, default='')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.Integer, nullable=False)
    job_params = db.Column(db.Text)
    progress = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, nullable=False)
    explain = db.Column(db.String(512), nullable=False, default='')


    created_time = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)

    sub_jobs = db.relationship('SubJob', backref="job", lazy='dynamic')

    def __init__(self, user=None, type=None, name='', job_params=None, status=None, explain='', created_time=None, start_time=None, finish_time=None, progress=0, id=None, user_id=None, from_cache=False, *args, **kwargs):
        self.id = id
        self.name = name
        self.user_id = user.id if user else user_id
        self.type = type
        job_params = {} if job_params is None else job_params
        self.job_params = json.dumps(job_params) if isinstance(job_params, (dict, )) else job_params
        self.progress = progress
        self.status = self.STATUS_WATING if status is None else status
        self.explain = explain
        self.created_time = timezone.now() if created_time is None else created_time
        self.start_time = start_time
        self.finish_time = finish_time
        self.from_cache = from_cache


    @property
    def job_params_object(self):
        try:
            return json.loads(self.job_params)
        except BaseException as e:
            return {}

    @classmethod
    def create(cls, user, type, name, job_params):
        job = cls(user=user, type=type, name=name, job_params=job_params)
        db.session.add(job)
        db.session.commit()
        redis.hmset(REDIS_KEYS['JOB_CONTENT'].format(id=job.id), job.as_dict_string())
        redis.lpush(REDIS_KEYS['JOB_PREPROCESS'], job.id)
        return job


    def preprocess(self):
        job = self
        if getattr(self, 'from_cache', False):
            job = self.get_by_key(self.id)
        job.status = self.STATUS_PREPROCESS
        job.progress = self.PROGRESS_PREPROCESS
        db.session.add(job)
        db.session.commit()
        redis.hmset(REDIS_KEYS['JOB_CONTENT'].format(id=self.id), {'status' : self.STATUS_PREPROCESS, 'progress' : self.PROGRESS_PREPROCESS})
        redis.lpush(REDIS_KEYS['JOB_DOING'], self.id)

    def start(self):
        job = self
        if getattr(self, 'from_cache', False):
            job = self.get_by_key(self.id)
        if job.start_time is None:
            job.start_time = timezone.now()
        job.status = self.STATUS_DOING
        redis_content = {'status' : self.STATUS_DOING}
        if job.progress < self.PROGRESS_DOING:
            job.progress = self.PROGRESS_DOING
            redis_content['progress'] = self.PROGRESS_DOING
        db.session.add(job)
        db.session.commit()
        redis.hmset(REDIS_KEYS['JOB_CONTENT'].format(id=self.id), {'status' : self.STATUS_DOING, 'progress' : self.PROGRESS_DOING})

    @classmethod
    def get_by_key(cls, value, key='id'):
        return db.session.query(cls).filter_by(**{key : value}).first()


    @classmethod
    def get_by_cache(cls, id):
        bjob = redis.hgetall(REDIS_KEYS['JOB_CONTENT'].format(id=id))
        if bjob:
            job = {'from_cache' : True}
            for k, v in bjob.items():
                job[k] = int(v) if k in ('id', 'user_id', 'type', 'progress', 'status') else v
            return cls(**job)
        return None


    def finish(self, status=None, explain=''):
        job = self
        if getattr(self, 'from_cache', False):
            job = self.get_by_key(self.id)

        job.finish_time = timezone.now()
        job.status = self.STATUS_SUCCESS if status is None else self.STATUS_FAILURE
        job.progress = self.PROGRESS_COMPLATE
        job.explain = explain
        db.session.add(job)
        db.session.commit()
        redis.delete(REDIS_KEYS['JOB_CONTENT'].format(id=self.id))
        redis.lrem(REDIS_KEYS['JOB_DOING'], 0, self.id)
        for _, key in JobType.KEYS.items():
            redis.delete(REDIS_KEYS['JOB_QUEUE'].format(type=key, id=self.id))

        return True


    def cancel(self):
        job = self
        if getattr(self, 'from_cache', False):
            job = self.get_by_key(self.id)
        job.status = self.STATUS_CANCEL
        job.progress = self.PROGRESS_COMPLATE
        SubJob.cancel(job)
        db.session.add(job)
        db.session.commit()
        redis.delete(REDIS_KEYS['JOB_CONTENT'].format(id=self.id))
        redis.lrem(REDIS_KEYS['JOB_DOING'], 0, self.id)
        for _, key in JobType.KEYS.items():
            redis.delete(REDIS_KEYS['JOB_QUEUE'].format(type=key, id=self.id))

        return True


    def delete(self):
        job = self
        if getattr(self, 'from_cache', False):
            job = self.get_by_key(self.id)
        job.status = self.STATUS_DELETE
        job.progress = self.PROGRESS_COMPLATE
        SubJob.delete(job)
        db.session.add(job)
        db.session.commit()
        redis.delete(REDIS_KEYS['JOB_CONTENT'].format(id=self.id))
        redis.lrem(REDIS_KEYS['JOB_DOING'], 0, self.id)
        for _, key in JobType.KEYS.items():
            redis.delete(REDIS_KEYS['JOB_QUEUE'].format(type=key, id=self.id))

        return True


    def doing(self, progress=None):
        job = self
        if getattr(self, 'from_cache', False):
            job = self.get_by_key(self.id)

        job.status = self.STATUS_DOING
        if progress is not None:
            job.progress = progress
        db.session.add(job)
        db.session.commit()



class SubJob(db.Model, AsDictMixin):

    STATUS_WATING = 1
    STATUS_DOING = 2
    STATUS_CANCEL = 3
    STATUS_SUCCESS = 4
    STATUS_FAILURE = 5
    STATUS_DELETE = 6

    id = db.Column(db.BigInteger, primary_key=True)
    job_id = db.Column(db.BigInteger, db.ForeignKey('job.id'))
    type = db.Column(db.Integer, nullable=False)
    job_params = db.Column(db.Text)
    created_time = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)

    executor = db.Column(db.String(128), nullable=False, default='')

    explain = db.Column(db.String(512), nullable=False, default='')

    def __init__(self, job, type, job_params=None, created_time=None, start_time=None, finish_time=None, status=None, executor='', explain='', *args, **kwargs):
        self.job_id = job.id
        self.type = type
        job_params = {} if job_params is None else job_params
        self.job_params = json.dumps(job_params) if isinstance(job_params, (dict, )) else job_params
        self.created_time = timezone.now() if created_time is None else created_time
        self.start_time = start_time
        self.finish_time = finish_time
        self.status = self.STATUS_WATING if status is None else status
        self.executor = executor
        self.explain = explain


    @property
    def job_params_object(self):
        try:
            return json.loads(self.job_params)
        except BaseException as e:
            return {}

    @classmethod
    def create(cls, job, type, job_params):
        sub_job = cls(job=job, type=type, job_params=job_params)
        db.session.add(sub_job)
        db.session.commit()
        redis.zadd(REDIS_KEYS['JOB_QUEUE'].format(type=JobType.KEYS.get(type), id=job.id), 0, sub_job.id)
        return sub_job

    @classmethod
    def get_by_key(cls, value, key='id'):
        return db.session.query(cls).filter_by(**{key : value}).first()


    @classmethod
    def cancel(cls, job):
        for obj in cls.query.filter(cls.job_id==job.id, cls.status.notin_([cls.STATUS_SUCCESS, cls.STATUS_CANCEL, cls.STATUS_FAILURE, cls.STATUS_DELETE])).all():
            obj.status = cls.STATUS_CANCEL
            Executor.running_decr_by_ident(obj.executor, obj.type)
            db.session.add(obj)
            db.session.commit()
        return True

    @classmethod
    def delete(cls, job):
        for obj in cls.query.filter(cls.job_id==job.id, cls.status.notin_([cls.STATUS_SUCCESS, cls.STATUS_CANCEL, cls.STATUS_FAILURE, cls.STATUS_DELETE])).all():
            obj.status = cls.STATUS_DELETE
            Executor.running_decr_by_ident(obj.executor, obj.type)
            db.session.add(obj)
            db.session.commit()
        return True


    def start(self, executor=None):
        self.status = self.STATUS_DOING
        self.executor = executor if executor else self.executor
        self.start_time = timezone.now()
        redis.zadd(REDIS_KEYS['JOB_QUEUE'].format(type=JobType.KEYS.get(self.type), id=self.job.id), -1, self.id)
        self.job.start()
        db.session.add(self)
        db.session.commit()


    def finish(self, status=None, explain=''):
        if self.status not in [self.STATUS_SUCCESS, self.STATUS_CANCEL, self.STATUS_FAILURE, self.STATUS_DELETE]:
            Executor.running_decr_by_ident(self.executor, self.type)

        self.status = self.STATUS_SUCCESS if status is None else status
        self.finish_time = timezone.now()
        self.explain = explain
        db.session.add(self)
        db.session.commit()
        redis.zadd(REDIS_KEYS['JOB_QUEUE'].format(type=JobType.KEYS.get(self.type), id=self.job.id), 1, self.id)


class SubJobResult(db.Model):

    STATUS_OK = 1
    STATUS_DELETE = 2

    id = db.Column(db.BigInteger, primary_key=True)
    sub_job_id = db.Column(db.BigInteger, db.ForeignKey('sub_job.id'))
    result = db.Column(db.Text)
    created_time = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, sub_job, result, created_time=None, status=None):
        self.sub_job_id = sub_job.id
        self.result = json.dumps(result) if isinstance(result, (dict, list, tuple, )) else result
        self.created_time = timezone.now() if created_time is None else created_time
        self.status = self.STATUS_OK if status is None else status

    @classmethod
    def create(cls, sub_job, result):
        job_result = cls(sub_job=sub_job, result=result)
        db.session.add(job_result)
        db.session.commit()
        return job_result


class Executor(db.Model, AsDictMixin):

    STATUS_OK = 1
    STATUS_DELETE = 2

    id = db.Column(db.Integer, primary_key=True)
    ident = db.Column(db.String(128), nullable=False, default='')
    hostname = db.Column(db.String(128), nullable=False, default='')
    pid = db.Column(db.Integer, nullable=False, default=0)

    type = db.Column(db.Integer, nullable=False, default=0)

    total = db.Column(db.Integer, nullable=False, default=0)
    busy = db.Column(db.Integer, nullable=False, default=0)
    idle = db.Column(db.Integer, nullable=False, default=0)

    created_time = db.Column(db.DateTime)
    heartbeat_time = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, ident, hostname, pid, type, total=0, busy=0, idle=0, running=0, created_time=None, heartbeat_time=None, status=None):
        self.ident = ident
        self.hostname = hostname
        self.pid = pid
        self.type = type
        self.total = total
        self.busy = busy
        self.idle = idle
        self.created_time = timezone.now() if created_time is None else created_time
        self.heartbeat_time = heartbeat_time
        self.status = self.STATUS_OK if status is None else status

    @classmethod
    def stats(cls):
        return {
            'total' : db.session.query(cls).filter(cls.status==cls.STATUS_OK).count(),
            'online' : db.session.query(cls).filter(cls.status==cls.STATUS_OK, cls.heartbeat_time >= timezone.now() - timedelta(minutes=3)).count()
        }

    @property
    def inuse(self):
        return max(self.busy, self.running)

    @property
    def type_text(self):
        texts = {
            2 : '资产发现',
            3 : '漏洞扫描',
        }
        return texts.get(self.type)


    @property
    def running(self):
        key = '{ident}:{type}'.format(ident=self.ident, type=self.type)
        value = redis.hget(REDIS_KEYS['JOB_EXECUTOR_RUNNING'], key)
        return 0 if value is None else int(value)


    def running_incr(self):
        key = '{ident}:{type}'.format(ident=self.ident, type=self.type)
        return redis.hincrby(REDIS_KEYS['JOB_EXECUTOR_RUNNING'], key, 1)


    def running_decr(self):
        key = '{ident}:{type}'.format(ident=self.ident, type=self.type)
        return redis.hincrby(REDIS_KEYS['JOB_EXECUTOR_RUNNING'], key, -1)


    @classmethod
    def running_decr_by_ident(cls, ident, type):
        obj = cls.query.filter_by(ident=ident, type=type).first()
        if obj:
            obj.running_decr()
        return True


    @classmethod
    def all(cls, online=True):
        query = db.session.query(cls).filter(cls.status==cls.STATUS_OK)
        if online:
            query = query.filter(cls.heartbeat_time >= timezone.now() - timedelta(minutes=3))
        return query.all()


    @classmethod
    def create(cls, ident, hostname, pid, type, total, busy, idle):
        executor = cls.query.filter_by(ident=ident, type=type).first()
        if executor is None:
            executor = cls(ident=ident, hostname=hostname, pid=pid, type=type, total=total, busy=busy, idle=idle)

        executor.total = total
        executor.busy = busy
        executor.pid = pid
        executor.heartbeat_time = timezone.now()
        db.session.add(executor)
        db.session.commit()
        return executor


    @classmethod
    def get_by_key(cls, value, key='id'):
        return db.session.query(cls).filter_by(**{key : value}).first()


    def execute(self, sub_job):
        self.running_incr()
        key = REDIS_KEYS['JOB_EXECUTOR'].format(type=sub_job.type, ident=self.ident)
        redis.lpush(key, json.dumps(sub_job.as_dict()))
        sub_job.start(self.ident)
        return True


    def as_dict(self):
        rt = super(Executor, self).as_dict()
        rt['running'] = self.running
        return rt


    @classmethod
    def delete_by_key(cls, id):
        executor = cls.get_by_key(id)
        if executor:
            executor.status = cls.STATUS_DELETE
            db.session.add(executor)
            db.session.commit()

        return True

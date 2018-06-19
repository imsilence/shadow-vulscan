#encoding: utf-8

import json
import logging
import traceback
from datetime import timedelta

from shadow import db, redis, REDIS_KEYS
from shadow.models import AsDictMixin
from shadow.validators import ValidatorMixin, ValidatorException

from schedule.models import Job, JobType
from utils import timezone

logger = logging.getLogger(__name__)

class SysVulJob(object):

    @classmethod
    def all(cls):
        return Job.query.filter(Job.type==JobType.SYS_VULSCAN, Job.status!=Job.STATUS_DELETE).all()

    @classmethod
    def get_by_key(cls, id):
        return Job.query.filter_by(id=id).filter(Job.type==JobType.SYS_VULSCAN, Job.status!=Job.STATUS_DELETE).first()

    @classmethod
    def create(cls, user, name, ip, concurrent_discover, concurrent_check, plugins):
        job_params = {
            'ip' : ip,
            'concurrent' : {
                'discover' : concurrent_discover,
                'check' : concurrent_check,
            },
            'plugins' : plugins
        }
        return Job.create(user=user, type=JobType.SYS_VULSCAN, name=name, job_params=job_params)


    @classmethod
    def cancel(cls, id):
        job = Job.get_by_key(id)
        return job.cancel() if job else False


    @classmethod
    def delete(cls, id):
        job = Job.get_by_key(id)
        return job.delete() if job else False


class SysVulPlugin(db.Model, ValidatorMixin, AsDictMixin):
    STATUS_OK = 1
    STATUS_DELETE = 2

    LEVEL_HEIGHT = 10
    LEVEL_MEDIUM = 6
    LEVEL_LOW = 1

    TYPE_SCRIPT = 'script'
    TYPE_SOCKET = 'socket_request'
    TYPE_HTTP = 'http_request'

    id = db.Column(db.BigInteger, primary_key=True)
    ident = db.Column(db.String(128), nullable=False, default='')
    name = db.Column(db.String(128), nullable=False, default='')
    level = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(128), nullable=False, default='')
    params = db.Column(db.Text)
    remark = db.Column(db.Text)
    links = db.Column(db.Text)
    created_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, ident=None, name=None, level=None, type=None, params=None, remark=None, links=None, created_time=None, status=None, id=None, from_cache=False):
        self.id = id
        self.ident =ident
        self.name = name
        self.level = level
        self.type = type
        self.params = params
        self.remark = remark
        self.links = links
        self.created_time = timezone.now() if created_time is None else created_time
        self.status = self.STATUS_OK if status is None else status

    @property
    def params_object(self):
        try:
            return json.loads(self.params)
        except BaseException as e:
            logger.exception(e)
            logger.error(traceback.format_exc())
            return {}

    @classmethod
    def all(cls):
        return db.session.query(cls).filter(cls.status != cls.STATUS_DELETE).all()


    @classmethod
    def get_by_key(cls, value, key='id', all=False):
        params = {key:value}
        if not all:
            params['status'] = cls.STATUS_OK
        return cls.query.filter_by(**params).first()

    def to_cache(self, clear=False):
        if clear:
            redis.delete(REDIS_KEYS['PLUGIN_SYS_VUL'].format(ident=self.ident))
        else:
            redis.hmset(REDIS_KEYS['PLUGIN_SYS_VUL'].format(ident=self.ident), self.as_dict_string())
        return True

    @classmethod
    def get_by_cache(cls, ident):
        bplugin = redis.hgetall(REDIS_KEYS['PLUGIN_SYS_VUL'].format(ident=ident))
        if bplugin:
            plugin = {'from_cache' : True}
            for k, v in bplugin.items():
                plugin[k] = int(v) if k in ('id', 'level', 'status') else v

            return cls(**plugin)
        return None


    def clean(self):

        obj = self.get_by_key(self.name, 'name')
        if self.id:
            if int(self.id) != int(obj.id):
                raise ValidatorException('名称已经存在')
        elif obj:
            raise ValidatorException('名称已经存在')

        obj = self.get_by_key(self.ident, 'ident')
        if self.id:
            if int(self.id) != int(obj.id):
                raise ValidatorException('标识已经存在')
        elif obj:
            raise ValidatorException('标识已经存在')


    @classmethod
    def create_or_replace(cls, ident, name, level, type, params, remark, links, id=None):
        obj = None
        if id:
            obj = cls.get_by_key(id)

        if obj is None:
            obj = cls()

        obj.ident = ident.strip()
        obj.name = name.strip()
        obj.level = level
        obj.type = type
        obj.params = json.dumps(params) if isinstance(params, (dict, )) else params
        obj.remark = remark.strip()
        obj.links = links.strip()
        obj.status = cls.STATUS_OK

        has_error, errors = obj.valid()
        if has_error:
            return None, has_error, errors

        db.session.add(obj)
        db.session.commit()
        obj.to_cache()
        return obj, has_error, errors


    @classmethod
    def delete(cls, id):
        obj = cls.get_by_key(id)
        if obj:
            obj.status = cls.STATUS_DELETE
            db.session.add(obj)
            db.session.commit()
            obj.to_cache(True)
        return obj


class PluginConfig(db.Model, ValidatorMixin, AsDictMixin):
    STATUS_OK = 1
    STATUS_DELETE = 2

    id = db.Column(db.BigInteger, primary_key=True)
    key = db.Column(db.String(64), nullable=False, default='')
    value = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.Integer, nullable=False)
    created_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, key, value=None, status=None, created_time=None, from_cache=False, id=None):
        self.id = id
        self.key = key
        self.value = value
        self.status = self.STATUS_OK if status is None else status
        self.created_time = timezone.now() if created_time is None else created_time
        self.from_cache = from_cache

    def clean(self):
        obj = self.get_by_key(self.key, 'key')
        if self.id:
            if int(self.id) != int(obj.id):
                raise ValidatorException('键已经存在')
        elif obj:
            raise ValidatorException('键已经存在')

    @property
    def value_object(self):
        try:
            return json.loads(self.value)
        except BaseException as e:
            return self.value

    @classmethod
    def all(cls):
        return cls.query.filter(cls.status!=cls.STATUS_DELETE).all()

    @classmethod
    def get_by_key(cls, value, key='id', all=False):
        params = {key:value}
        if not all:
            params['status'] = cls.STATUS_OK
        return cls.query.filter_by(**params).first()

    @classmethod
    def create_or_replace(cls, key, value, id=None):
        obj = None
        if id:
            obj = cls.get_by_key(id)

        if obj is None:
            obj = cls(key=key)

        obj.value = value.strip()
        obj.status = cls.STATUS_OK

        has_error, errors = obj.valid()

        if has_error:
            return None, has_error, errors

        db.session.add(obj)
        db.session.commit()
        obj.to_cache()
        return obj, has_error, errors

    def to_cache(self, clear=False):
        if clear:
            redis.delete(REDIS_KEYS['PLUGIN_CONFIG'].format(ident=self.key))
        else:
            redis.hmset(REDIS_KEYS['PLUGIN_CONFIG'].format(ident=self.key), self.as_dict_string())
        return True

    @classmethod
    def get_by_cache(cls, key):
        bconfig = redis.hgetall(REDIS_KEYS['PLUGIN_CONFIG'].format(ident=key))
        if bconfig:
            plugin = {'from_cache' : True}
            for k, v in bconfig.items():
                plugin[k] = int(v) if k in ('id', 'status') else v
            return cls(**plugin)

        return None


    @classmethod
    def delete(cls, id):
        obj = cls.get_by_key(id)
        if obj:
            obj.status = cls.STATUS_DELETE
            db.session.add(obj)
            db.session.commit()
            obj.to_cache(True)
        return obj


class AssetSysVul(db.Model, AsDictMixin):
    id = db.Column(db.BigInteger, primary_key=True)
    ip = db.Column(db.String(256), nullable=False)
    plugin_ident = db.Column(db.String(128), nullable=False)
    payloads = db.Column(db.Text)
    created_time = db.Column(db.DateTime, nullable=False)
    last_discover_time = db.Column(db.DateTime, nullable=False)

    @classmethod
    def stats(cls):
        return {
            'total' : cls.query.count(),
            '24_hour' : cls.query.filter(cls.created_time>=timezone.now() - timedelta(days=1)).count(),
        }

    @classmethod
    def stats_host_vul(cls, topn=10):
        rs = db.session.execute('select ip, count(*) from asset_sys_vul group by ip  order by count desc limit :topn', {'topn':topn})
        return [dict(r) for r in rs]

    @classmethod
    def stats_vul_host(cls, topn=10):
        rs = db.session.execute('select plugin_ident, count(*) from asset_sys_vul group by plugin_ident order by count desc limit :topn', {'topn':topn})
        return [dict(r) for r in rs]

    @classmethod
    def create_or_replace(cls, key, plugin_ident, payloads):
        obj = cls.query.filter_by(ip=key, plugin_ident=plugin_ident).first()
        if obj is None:
            obj = cls()
            obj.ip = key
            obj.plugin_ident = plugin_ident
            obj.created_time = timezone.now()

        obj.last_discover_time = timezone.now()
        obj.payloads = json.dumps(payloads) if isinstance(payloads, (list, dict)) else payloads
        db.session.add(obj)
        db.session.commit()

    @classmethod
    def delete_not_found(cls, key, now):
        cls.query.filter(cls.ip==key, cls.last_discover_time<now).delete()

    @classmethod
    def all(cls, key=None):
        query = cls.query
        if key:
            query = query.filter_by(ip=key)
        return query.all()
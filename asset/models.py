#encoding: utf-8

import logging
import traceback
from datetime import timedelta

from shadow import db
from shadow.models import AsDictMixin

from utils import timezone

logger = logging.getLogger(__name__)

class SysGroup(db.Model):
    STATUS_OK = 0
    STATUS_DELETE = 1

    id = db.Column(db.BigInteger, primary_key=True)
    pid = db.Column(db.BigInteger, nullable=False)
    name = db.Column(db.String(32), nullable=False, default='')
    created_time = db.Column(db.DateTime, nullable=False)

    manager = db.Column(db.String(64), nullable=False, default='')

    status = db.Column(db.Integer, nullable=False)

    assets = db.relationship('SysAsset', backref="group", lazy="dynamic")


class SysAsset(db.Model, AsDictMixin):
    WEIGHT_HIGH = 10
    WEIGHT_MEDIUM = 6
    WEIGHT_LOW = 1

    STATUS_NEW = 0
    STATUS_ACK = 1
    STATUS_DELETE = 2

    id = db.Column(db.BigInteger, primary_key=True)
    sn = db.Column(db.String(128), nullable=False, default='')
    name = db.Column(db.String(32), nullable=False, default='')
    ip = db.Column(db.String(256), nullable=False, default='')
    mac = db.Column(db.String(32), nullable=False, default='')
    os = db.Column(db.String(128), nullable=False, default='')
    group_id = db.Column(db.BigInteger, db.ForeignKey('sys_group.id'))

    manager = db.Column(db.String(64), nullable=False, default='')

    weight = db.Column(db.Integer, nullable=False)

    created_time = db.Column(db.DateTime, nullable=False)
    last_discove_time = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.Integer, nullable=False)
    applications = db.relationship('Application', backref='asset', lazy='dynamic')

    @classmethod
    def stats(cls):
        return {
            'total' : cls.query.filter(cls.status.notin_([cls.STATUS_DELETE])).count(),
            '24_hour' : cls.query.filter(cls.created_time>=timezone.now() - timedelta(days=1), cls.status.notin_([cls.STATUS_DELETE])).count(),
        }

    @classmethod
    def all(cls):
        return cls.query.filter(cls.status.notin_([cls.STATUS_DELETE])).all()

    @classmethod
    def get_by_key(cls, value, key='id'):
        return db.session.query(cls).filter_by(**{key : value}).first()

    @classmethod
    def create_or_replace(cls, **kwargs):
        ip = kwargs.get('ip', '')
        obj = cls.get_by_key(ip, key='ip')
        try:

            if obj is None or obj.status == cls.STATUS_DELETE:
                obj = cls()
                obj.ip = ip
                obj.status = cls.STATUS_NEW
                obj.created_time = timezone.now()
                obj.weight = cls.WEIGHT_LOW

            obj.last_discove_time = timezone.now()
            obj.name = kwargs.get('name', obj.name)
            obj.os = kwargs.get('os', obj.os)
            obj.mac = kwargs.get('mac', obj.mac)

            db.session.add(obj)
            db.session.commit()

            for app in kwargs.get('apps', []):
                Application.create_or_replace(app.get('name', ''),
                    app.get('protocol', ''),
                    app.get('port', 0),
                    app.get('state', ''),
                    app.get('product', ''),
                    app.get('version', ''),
                    obj,
                )
        except BaseException as e:
            logger.error(e)
            logger.exception(traceback.format_exc())
            db.session.rollback()

        return obj

    @classmethod
    def delete_by_key(cls, id):
        obj = cls.get_by_key.get(id)
        if obj:
            obj.status = cls.STATUS_DELETE
            db.session.add(obj)
            db.session.commit()

        return obj


class Application(db.Model):
    STATUS_NEW = 0
    STATUS_ACK = 1
    STATUS_DELETE = 2

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(128), nullable=False, default='')

    protocol = db.Column(db.String(32), nullable=False, default='')
    port = db.Column(db.Integer, nullable=False, default=0)
    state = db.Column(db.String(32), nullable=False, default='')

    product = db.Column(db.String(128), nullable=False, default='')
    version = db.Column(db.String(64), nullable=False, default='')

    asset_id = db.Column(db.BigInteger, db.ForeignKey('sys_asset.id'))

    created_time = db.Column(db.DateTime, nullable=False, default='')
    last_discove_time = db.Column(db.DateTime, nullable=False, default='')
    status = db.Column(db.Integer, nullable=False)

    @classmethod
    def stats(cls):
        return {
            'total' : cls.query.filter(cls.status.notin_([cls.STATUS_DELETE])).count(),
            '24_hour' : cls.query.filter(cls.created_time>=timezone.now() - timedelta(days=1), cls.status.notin_([cls.STATUS_DELETE])).count(),
        }

    @classmethod
    def stats_port(cls):
        rs = db.session.execute('select port, count(*) from application where status != :status group by port order by count desc', {'status' : cls.STATUS_DELETE})
        return [dict(r) for r in rs]

    @classmethod
    def all(cls):
        return cls.query.filter(cls.status.notin_([cls.STATUS_DELETE])).all()

    @classmethod
    def create_or_replace(cls, name, protocol, port, state, product, version, asset, *args, **kwargs):
        obj = db.session.query(cls).filter_by(asset_id=asset.id, port=port).first()
        if obj is None or obj.status == cls.STATUS_DELETE:
            obj = cls()
            obj.port = port
            obj.created_time = timezone.now()
            obj.status = cls.STATUS_NEW
            obj.asset_id = asset.id

        obj.name = name
        obj.protocol = protocol
        obj.state = state
        obj.product = product
        obj.last_discove_time = timezone.now()

        db.session.add(obj)
        db.session.commit()


class WebGroup(db.Model):
    STATUS_OK = 0
    STATUS_DELETE = 1

    id = db.Column(db.BigInteger, primary_key=True)
    pid = db.Column(db.BigInteger, nullable=False)
    name = db.Column(db.String(32), nullable=False, default='')
    created_time = db.Column(db.DateTime, nullable=False)

    manager = db.Column(db.String(64), nullable=False, default='')

    status = db.Column(db.Integer, nullable=False)

    assets = db.relationship('WebAsset', backref="group", lazy="dynamic")


class WebAsset(db.Model):
    STATUS_NEW = 0
    STATUS_ACK = 1
    STATUS_OFFLINE = 2
    STATUS_DELETE = 3

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(32), nullable=False, default='')
    url = db.Column(db.String(256), nullable=False, default='')

    group_id = db.Column(db.BigInteger, db.ForeignKey('web_group.id'))
    sys_asset_id = db.Column(db.BigInteger, db.ForeignKey('sys_asset.id'))

    manager = db.Column(db.String(64), nullable=False, default='')

    created_time = db.Column(db.DateTime, nullable=False, default='')
    last_discove_time = db.Column(db.DateTime, nullable=False, default='')

    status = db.Column(db.Integer, nullable=False)

    @classmethod
    def all(cls):
        return cls.query.filter(cls.status.notin_([cls.STATUS_DELETE])).all()



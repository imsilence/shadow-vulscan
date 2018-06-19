#encoding: utf-8

from werkzeug.security import check_password_hash, generate_password_hash

from shadow import db
from utils import timezone

from shadow.validators import ValidatorMixin, ValidatorUtils, ValidatorException



class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=True, default='')
    type = db.Column(db.Integer, nullable=True, default=0)

    created_time = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.Integer, nullable=False, default=0)

    users = db.relationship('User', backref='role', lazy='dynamic')



class User(db.Model, ValidatorMixin):
    STATUS_REGISTED = 0
    STATUS_LOCKED = 1
    STATUS_OK = 2
    STATUS_DELETE = 3

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, default='')
    password = db.Column(db.String(512), nullable=False, default='')
    email = db.Column(db.String(64), nullable=False, default='')

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    created_time = db.Column(db.DateTime, nullable=False)
    last_login_time = db.Column(db.DateTime)

    is_super = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.Integer, nullable=False)


    def __init__(self, name, email, is_super=False, created_time=None, last_login_time=None, status=None, id=None, password=None, role_id=None):
        self.id = id
        self.name = name
        self.password = password
        self.email = email
        self.role_id = role_id
        self.created_time = created_time if created_time else timezone.now()
        self.last_login_time = last_login_time
        self.is_super = is_super
        self.status =  self.STATUS_REGISTED if status is None else status

    @classmethod
    def authenticate(cls, name, password):
        user = cls.query.filter_by(name=name).first()
        if not user:
            user = cls.query.filter_by(email=name).first()

        if user and check_password_hash(user.password, password):
            user.last_login_time = timezone.now()
            db.session.add(user)
            db.session.commit()
            return user

        return None


    def set_password(self, password):
        self.password = generate_password_hash(password)


    def clean_name(self):
        name = self.name.strip()
        if not ValidatorUtils.is_length(name, 3, 32):
            raise ValidatorException('用户名必须为3到32个字符')

        user = User.query.filter_by(name=self.name).first()

        if user and (self.id is None or user.id != self.id):
            raise ValidatorException('用户名已存在')

        return name

    def clean_email(self):
        email = self.email.strip()
        if not ValidatorUtils.is_email(email):
            raise ValidatorException('邮箱格式不正确')

        user = User.query.filter_by(email=self.email).first()
        if user and (self.id is None or user.id != self.id):
            raise ValidatorException('邮箱已存在')

        return email


    @classmethod
    def create(cls, name, password, email, is_super):
        user = cls(name=name, email=email, is_super=is_super, status=cls.STATUS_OK)
        user.set_password(password)

        has_error, errors = user.valid()

        if has_error:
            return None, has_error, errors

        db.session.add(user)
        db.session.commit()
        return user, has_error, errors



    @classmethod
    def get_by_key(cls, value, key='id'):
        return cls.query.filter_by(**{key:value}).first()


    @classmethod
    def all(cls):
        return cls.query.filter(cls.status!=cls.STATUS_DELETE).all()
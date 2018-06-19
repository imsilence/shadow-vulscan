#encoding: utf-8

REDIS_KEYS = {
    'JOB_PREPROCESS' : 'shadow:job:preprocess',
    'JOB_CONTENT' : 'shadow:job:content:{id}',
    'JOB_DOING' : 'shadow:job:doing',
    'JOB_QUEUE' : 'shadow:job:{type}:{id}',
    'JOB_EXECUTOR' : 'shadow:job:executor:{type}:{ident}',
    'JOB_EXECUTOR_RUNNING' : 'shadow:job:executor:running',
    'JOB_RESULT' : 'shadow:job:result',
    'PLUGIN_SYS_VUL' : 'shadow:plugin:sys_vul:{ident}',
    'PLUGIN_CONFIG' : 'shadow:plugin:config:{ident}',
}

DEFAULT_CONCURRENT = 3

class AppConfig(object):
    SECRET_KEY = b'\x98\t\x11t\x97\x9d4.+\xe5Z\xb39\xe8/\xd2\xfc\xf3\xa1\xe2\xeb\xc4\xdbr,E\x06|\xec\xb9\x05d'

    #SQLALCHEMY_DATABASE_URI = 'mysql://{user}:{password}@{host}:{port}/shadow?charset=utf8'.format(user='root', password='password', host='localhost', port=3306)
    SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}:{port}/shadow'.format(user='silence', password='password', host='localhost', port=5432)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS = {
        'host' : 'localhost',
        'port' : 6379,
        'db' : 0,
        'password' : '',
        'decode_responses' : True,
        #'password' : 'password',
    }
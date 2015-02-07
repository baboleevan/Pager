# -*- coding: utf-8 -*-
from os import environ 
from os.path import dirname
from socket import gethostname
from datetime import timedelta


class Production(object):
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2:///pager'
    ASSETS_DEBUG = DEBUG = environ.get('DEBUG', False) and True or False
    FACEBOOK_ID = '434030416667463'
    FACEBOOK_SECRET= '9a20f99a92ea341617f5370582b9f6d7'
    SQLALCHEMY_ECHO = environ.get('SQLALCHEMY_ECHO', None)
    SECRET_KEY = ':\x84\x97\xd5\xf6lO"P6\xdeYb?:\x83y\'' \
        'xf7\xbb\x9e\x84\x03Y\xc0g\xd4vu\xe2C\xc0>'

    BASE_URL = 'http://pager.funnyplan.com/'
    SMTP_SERVER = 'localhost'

    # celery configs
    BROKER_URL = 'redis://localhost'

    # 부재중 알림 메시지 발송 대기 시간 
    # 가장 오래된 부재중 메시지가 30분이 지났을때 발송한다.
    ABSECE_MAIL_HOLD_DOWN = timedelta(minutes=30)


class Develope(Production):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + dirname(__file__) + '/../pager.sqlite'
    FACEBOOK_ID = '426630354080168'
    FACEBOOK_SECRET = '46411b6f77ffd9507f47492a5cc0c1b9'
    BASE_URL = 'http://localhost:5000/'


class Gyuri(Develope):
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://localhost/pager'
    FACEBOOK_ID = '579087202120185'
    FACEBOOK_SECRET = '9e0f7354297fe1175e2473a1142ed953'
    BASE_URL = 'http://192.168.0.100:5000/'


configs = {'gyuri.local': Gyuri, 'Develope': Develope, 'Production': Production}

config_from_env = environ.get('PAGER_CONFIG', None)
if config_from_env:
    config = configs.get(config_from_env)
else:
    hostname = gethostname()
    config = configs.get(hostname, Production)
config = config()

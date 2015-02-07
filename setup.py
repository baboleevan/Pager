from setuptools import setup

setup(
    name='pager',
    version='0.0.1',
    packages=['pager'],
    install_requires=[
        'Flask', 'Flask-Script', 'Flask-Assets', 'pyjade', 'Flask-WTF',
        'flask-modus', 'flask-debugtoolbar',
        'alembic','Flask-SQLAlchemy', 'psycopg2', 'psycogreen', 'pytz',
        'simplejson', 'yuicompressor', 'glob2',
        'gevent-socketio', 'facebook-sdk', 'gunicorn==0.16.1',
	'celery-with-redis',
    ]
)

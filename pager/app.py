import locale
from os import path, environ
from math import ceil
from logging import INFO, StreamHandler

from flask import Flask
from pyjade.ext.jinja import PyJadeExtension
from flask_debugtoolbar import DebugToolbarExtension

from pager.config import config
from pager.libs.timezone import now

app = Flask(__name__)
app.config.from_object(config)
app.jinja_env.add_extension(PyJadeExtension)
app.jinja_env.pyjade.options['pretty'] = 'JADE_PRETTY' in environ
app.node_bin_path = path.normpath(app.root_path + '/../node_modules/.bin')

if app.debug:
    toolbar = DebugToolbarExtension(app)
else:
	app.logger.addHandler(StreamHandler())
	app.logger.setLevel(INFO)


def minutes(timedelta):
    return int(ceil(timedelta.total_seconds() / 60.))

@app.context_processor
def _inject():
    return dict(xrange=xrange, hex=hex, now=now(), minutes=minutes, locale=locale)

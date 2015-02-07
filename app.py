#!venv/bin/python
from gevent import monkey; monkey.patch_all()

from pager.manager import manager

manager.run()

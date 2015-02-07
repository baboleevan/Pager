from flask.ext.script import Manager, Shell
from flask.ext.assets import ManageAssets
from socketio.server import SocketIOServer
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication

from pager import models, tasks
from pager.app import app
from pager.assets import env as assets_env


manager = Manager(app)
manager.add_command('assets', ManageAssets(assets_env))
def make_context():
    return dict(app=app, models=models)
manager.add_command('shell', Shell(make_context=make_context))

@manager.command
def runserver(bind='', port=5000):
    port = int(port)
    @run_with_reloader
    def run():
        print ' * serve on http://%s:%d' % (
            bind=='' and '127.0.0.1' or bind, port
        )
        SocketIOServer((bind, port), app).serve_forever()
    run()


@manager.command
def send_notify_mails(limit=0):
    limit = int(limit)
    tasks.send_notify_mails(limit)

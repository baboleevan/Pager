from flask import url_for
from flask.ext.assets import Environment, Bundle
from glob2 import glob

from pager.app import app
from pager.libs import trim_prefix, find_files
import filters #activate and register filters

def img(name, _external=False):
    return url_for('static', filename='img/' + name, _external=_external)

@app.context_processor
def inject():
    return dict(img=img)

env = Environment(app)
env.config['stylus_bin'] = app.node_bin_path + '/stylus'
env.config['iced_bin'] = app.node_bin_path + '/iced'
env.config['uglifyjs_bin'] = app.node_bin_path + '/uglifyjs'
stylus_extra_args = (
    '--include-css',
    '-I', app.static_folder + '/css',
)
if env.config['DEBUG']:
    stylus_extra_args += ('-l',)
env.config['stylus_extra_args'] = stylus_extra_args

pager_css_depends = trim_prefix(
    app.static_folder, find_files(app.static_folder + '/css')
)
pager_css = Bundle(
    'css/pager.styl', filters='stylus',
    depends=pager_css_depends, output='built/pager.css'
)

admin_css = Bundle(
    'css/admin.styl', filters='stylus', output='built/2nd_floor/admin.css'
)

vendor_js = Bundle(
    *map(lambda x: 'vendor/' + x, (
        'jquery-1.9.0.js', 'bootstrap.js', 'underscore.js', 'async.js',
        'knockout-2.2.1.debug.js', 'patches.js', 'jquery.ba-bbq.js',
        'jquery.popupWindow.js',
        'iced-coffee-script-runtime.js', 'underscore.string.js', 'moment.js',
        'hammer.js', 'jquery.hammer.js', 'one-color-all.js', 'path.js',
        'raven.js', 'locache.0.3.2.js',
    ))
)
vendor_js = Bundle(
    vendor_js,
    Bundle(
        'vendor/knockout.localStorage.iced',
        filters='iced', output='built/knockout.localStorage.js'
    )
)
requirify = Bundle(
    'vendor/requirify.iced', filters='iced', output='built/requirify.js'
)
vendor_js = Bundle(vendor_js, 'socket.io/socket.io.js', requirify)

pager_js = []
for js in trim_prefix(
    app.static_folder, find_files(app.static_folder + '/js')
):
    pager_js.append(
        Bundle(js, filters='iced,requirify', output='built/' + js + '.js')
    )
pager_js = Bundle(*pager_js)

admin_js = []
for js in trim_prefix(
    app.static_folder, find_files(app.static_folder + '/2nd_floor')
):
    admin_js.append(
        Bundle(js, filters='iced,requirify', output='built/' + js + '.js')
    )
admin_js = Bundle(*admin_js)

# register assets
env.register(
    'pager_css', 'css/reset.css', pager_css,
    filters='yui_css', output='built/pager_%(version)s.min.css'
)
env.register(
    'pager_js', vendor_js, pager_js,
    filters='static-uglifyjs', output='built/pager_%(version)s.min.js'
)
env.register(
    'admin_css', 'css/reset.css', 'css/bootstrap.css', admin_css,
    filters='yui_css', output='built/2nd_floor/admin_%(version)s.min.css'
)
env.register(
    'admin_js', vendor_js, admin_js,
    filters='static-uglifyjs', output='built/2nd_floor/admin_%(version)s.min.js'
)

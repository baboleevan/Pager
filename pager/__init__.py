from pager.app import app
from pager.admin import admin
import pager.routes
import pager.models
import pager.assets

app.register_blueprint(admin, url_prefix='/2nd_floor')

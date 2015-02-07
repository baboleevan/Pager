import os
from functools import wraps
from urllib import urlopen

from flask import request, render_template, flash, session

def templated(template=None, blueprint=None):
        def decorator(controller):
                @wraps(controller)
                def decorated(*args, **kwargs):
                        response = controller(*args, **kwargs)
                        if not isinstance(response, dict):
                                return response
                        template_name = template
                        if template_name is None:
                                template_name = request.endpoint.replace('.', '/')
                        if not os.path.splitext(template_name)[1]:
                                template_name += '.jade'
                        template_name = response.pop('_template', template_name)
                        return render_template(template_name, **response)
                return decorated
        if hasattr(template, '__call__'):
                controller, template = template, None
                return decorator(controller)
        return decorator
    
def blueprint_templated(blueprint_name):
    def blueprinted(template=None):
        return templated(template, blueprint_name)
    return blueprinted

def last_list_url(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session['last_list_url'] = request.url
        return f(*args, **kwargs)
    return decorated

def error(message):
    return flash(message, 'error')

def success(message):
    return flash(message, 'success')

def info(message):
    return flash(message, 'info')
# deploy with GEvent greenlet-- modify this port
# this should only be used in a temporary deployment scenario
# it works pretty well, but not necessarily hardened

from gevent.pywsgi import WSGIServer
import sys


from .utils import cli_arg_exists, cli_arg_value

# __init__.py
# This is the main app of FlaskPress Alpha

from flask import Flask
from .database import initialize, generate_meta_info
import os


###############
# Declare the app object and configuration from our file
app = Flask(__name__)
app.config.from_pyfile('app.cfg')
app.secret_key = app.config['SECRET_KEY']
os.chdir('fpress')

### DATABASE INITIALIZE, actually, we could embed the meta_info_call into the initialize
initialize(app) # create a database if needed
generate_meta_info() # create a meta collection (brand info, etc.)

### FlaskPress views
## Since we are focused on simplicity, views are put into logical python modules
## Future - convert these to Flask Blueprints

## INCLUDE ADMIN VIEWS
from . import admin_views

## INCLUDE LOGIN/LOGOUT/REGISTER VIEWS
from . import login_logout_views

## INCLUDE PAGE EDIT/DELETE/SEARCH
from . import page_views

## INCLUDE FILE UPLOAD HANDLERS (typically images)
from . import file_views

## INCLUDE main view and slug routing
from . import main_view

############ That's All Folks! ##############

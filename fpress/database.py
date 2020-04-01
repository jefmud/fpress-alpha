# initialize.py
from .users import create_user
from .utils import token_generator
import os

# Declare database as a TinyMongo Client
from tinymongo import TinyMongoClient
DB = TinyMongoClient().flaskpress

def initialize(app):
    """initialize the app, initialize configuration before app starts"""
    # we will modify the app config object some

    # this is called before the app starts

    # set up the base directory
    if app.config['BASE_DIR'] == '':
        app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))

    # UPLOAD FOLDER will have to change based on your own needs/deployment scenario
    if app.config['UPLOAD_FOLDER'] == '':
        #app.config['UPLOAD_FOLDER'] = os.path.join(app.config['BASE_DIR'], './uploads')
        app.config['UPLOAD_FOLDER'] = './uploads'

    # allowed file extensions of uploaded FILE
    if app.config['ALLOWED_EXTENSIONS'] == '':
        app.config['ALLOWED_EXTENSIONS'] = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
    else:
        if isinstance(app.config['ALLOWED_EXTENSIONS'], str):
            app.config['ALLOWED_EXTENSIONS'] = app.config['ALLOWED_EXTENSIONS'].split(',')

    # we're using a separte function because it has hashing and checking
    admin=app.config['ADMIN_USERNAME']
    password = token_generator()
    password = app.config['INITIAL_PASSWORD']
    # A USER is only created if it DOES NOT ALREADY EXIST!
    u  = create_user(DB, username=admin,
                     password=password,
                     is_admin=True)

    # These are the default HOME and ABOUT pages-- can be easily changed later.
    # will not overwrite existing home and about pages.
    p = DB.pages.find_one({'slug':app.config['FRONTPAGE_SLUG']})
    if p is None:
        # create only if page IS NOT present
        DB.pages.insert_one({'slug': app.config['FRONTPAGE_SLUG'], 'title':'Home', 'owner':admin,
                             'content':'<b>Welcome, please change me.</b>  I am the <i>default</i> Home page!',
                             'is_markdown':False, 'owner':'admin', 'show_nav':True, 'is_published': True})
        print("default HOME page created")

    p = DB.pages.find_one({'slug':'about'})
    if p is None:
        DB.pages.insert_one({'slug':'about', 'title':'About', 'owner':admin,
                             'content':'<b>Welcome</b>, please change me.  I am the <i>default</i> boilerplate About page.',
                             'is_markdown':False, 'owner':'admin', 'show_nav':True, 'is_published': True})
        print("default ABOUT page created")

    m = DB.meta.find_one({})
    if m is None:
        DB.meta.insert_one({'brand':'FlaskPress', 'theme':'default'})

def generate_meta_info():
    """generate meta information about categories and menu pages, store in database"""
    # this should only be called after a page is created or modified
    pages = DB.pages.find()
    categories = []
    menu = []
    for page in pages:
        if page.get('categories'):
            category_list = page.get('categories').split(',')
            categories.extend(category_list)
        if page.get('title_nav'):
            menu.append((page.get('title'),page.get('slug')))
    # get the meta information if it exists
    meta = DB.meta.find_one()
    meta['categories'] = list(set(categories))
    meta['menu'] = menu
    # update meta
    DB.meta.update_one({'_id':meta['_id']}, meta)

############### BLOG 2 META DEFAULTS #############
# currently unused legacy section
# once running, you can override these defaults
default_brand = "FlaskBlog"
default_about = """
<p>FlaskPress is an open-source micro content management system.
It is our hope it will be useful to someone in the community that have learned or are
discovering the excellence of Python and the Flask web framework.
</p>
<p>
FlaskPress leverages several Flask plugins and the simple TinyMongo to achieve a flat file storage system. The advantage of using
TinyMongo is simplicity and being a somewhat small/self-contained project.  The advantage of using Flask is it's unopinonated and
easy to deploy framework that is high extensible.
</p>
<p>
In addition, we leverage Jinja2 template language and we use the Bulma CSS framework for the front-end styling.  It should be relatively easy
for a developer to add their own templates and design framework, based on Skeleton, Bootstrap, Materialize, or some other excellent
framework.
</p>
<p>
We look forward to community involvement to add more to the project.
</p>
"""

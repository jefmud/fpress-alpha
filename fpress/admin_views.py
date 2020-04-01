from . import app
import os
from flask import (g, flash, redirect, render_template, request, send_file, session, url_for)
from .forms import CSRF
from .database import initialize, generate_meta_info
from .details import stylesheets
import json
import time
from .utils import admin_required, login_required
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from .zipper import Zipper

def posix_path(path, prefix=""):
    """convert a path to posix compatible path"""
    return prefix + path.replace('\\','/')

@app.route('/_admin/filescan')
@admin_required
def admin_uploads_sync():
    """syncs uploads to database (orphaned or manually uploaded files)"""
    # do a walk over the files and see which are NOT listed in current files collection
    found = False
    for (root,dirs,files) in os.walk(app.config['UPLOAD_FOLDER'], topdown=True):
        # if there are files in the subfolder, loop over them
        if files:
            for filename in files:
                # get the url/filepath
                abs_path = posix_path(os.path.normpath(root), prefix='/')
                url = posix_path(os.path.join(abs_path, filename))
                filepath = posix_path(os.path.join(os.path.split(root)[1], filename))\
                # does this file exist in collection?
                this_file = g.db.files.find_one({'url':url})
                if this_file is None:
                    # create a file object for the collection
                    file_object = {'title': filename, 'filepath': filepath, 'owner': g.username, 'url':url}
                    g.db.files.insert(file_object)
                    flash('found file {}'.format(url), category='info')
                    found = True
    if not found:
        flash("No orphaned files found.", category='info')
    return redirect(url_for('admin_files'))

@app.route('/_admin/users', methods=('GET','POST'))
@admin_required
def admin_users():
    """view for administering users"""
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )

    users = g.db.users.find()
    return render_template('admin_users.html', users=users)

@app.route('/_admin/user/add', strict_slashes=False)
@admin_required
def user_add():
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )
    """ADMIN-ONLY view to add a user"""
    return redirect(url_for('user_edit'))

@app.route('/_admin/user', methods=('GET','POST'), strict_slashes=False)
@app.route('/_admin/user/<user_id>', methods=('GET','POST'))
@admin_required
def user_edit(user_id=None):
    """ADMIN-ONLY view to edit a user or create a user if no user_id supplied"""
    if user_id is None:
        user = {}
    else:
        user = g.db.users.find_one({'_id':user_id})
        if user is None:
            flash("No such user with id={}".format(user_id), "warning")
            return redirect(url_for('admin_user'))

    form = CSRF()
    if form.validate_on_submit():
        username = request.form.get('username')
        displayname = request.form.get('displayname')
        email = request.form.get('email')
        password = request.form.get('password')
        is_active = request.form.get('is_active') == 'on'
        is_admin = request.form.get('is_admin') == 'on'

        if len(username) > 0 and len(password) > 0:
            user['username'] = username
            user['displayname'] = displayname

            if user.get('password') != password:
                # password changed, rehash the password
                user['password'] = generate_password_hash(password)

            user['email'] = email
            user['is_active'] = is_active
            user['is_admin'] = is_admin

            if user_id:
                g.db.users.update_one({'_id':user_id}, user)
                flash("User information changed", category="success")
            else:
                g.db.users.insert_one(user)
                flash("New user created", category="success")
            return redirect(url_for('admin_users'))
        else:
            flash('Username and password must be filled in', category="danger")

    return render_template('admin_user_edit.html', user=user, form=form)

@app.route('/_admin', methods=('GET','POST'), strict_slashes=False)
@admin_required
def admin():
    # in case of a search.
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )

    meta = g.db.meta.find_one()

    """view for basic admin tasks"""
    form = CSRF()
    if form.validate_on_submit():
        # get data from the form
        editor = request.form.get('editor')
        brand = request.form.get('brand')
        stylesheet = request.form.get('stylesheet')
        logo = request.form.get('logo')

        # set the global brand objects
        meta['brand'] = brand
        meta['logo'] = logo
        meta['editor'] = editor
        if stylesheet != 'site-default':
            meta['stylesheet'] = stylesheet

        g.db.meta.update_one({'_id':meta.get('_id')}, meta)
        # ensure the g vars match the current setting
        g.editor = editor
        g.brand = brand
        g.stylesheet = stylesheet
        return redirect(url_for('admin'))

    return render_template('admin.html', form=form, stylesheets=stylesheets)

@app.route('/_admin/page_export')
@admin_required
def admin_page_export():
    """EXPORT pages data only"""
    filename = 'pages.json'
    pages = list(g.db.pages.find())
    with open(filename,'w') as fout:
        json.dump(pages, fout)
    return send_file(filename, as_attachment=True)

@app.route('/_admin/export_database')
@admin_required
def admin_export_database():
    """EXPORT ENTIRE DATABASE"""
    database_json_file = "./tinydb/flaskpress.json"
    attachment_filename = '{}.flaskpress.json'.format(time.time())
    print(attachment_filename)
    return send_file(database_json_file, attachment_filename=attachment_filename, as_attachment=True)

@app.route('/_admin/export_uploads')
@admin_required
def admin_export_uploads():
    """administrator can export all uploaded content"""
    # initialize the zipper, upload folder config by user
    target_dir = app.config['UPLOAD_FOLDER']
    target_file = '{}.uploads.zip'.format(time.time())
    uploads = Zipper(target_dir)
    # save into top-level uploads.zip file
    uploads.save(target_file)
    return send_file(target_file, as_attachment=True)

@app.route('/_admin/import_database')
def admin_import_database():
    return render_template('admin_database_upload.html')

@app.route('/_admin/upload_database', methods=['POST'])
@admin_required
def database_upload_handler():
    """Database upload handling"""
    global DB
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and '.json' in file.filename.lower():
            # we are not checking the json, probably should look
            # to see if this is really a flaskpress backup!
            filename = secure_filename(file.filename)
            subfolder = './tinydb'
            pathname = os.path.join(subfolder, filename)
            # in reality, this is the ONLY name the file should have at the destination
            pathname = './tinydb/flaskpress.json'

            try:
                # finally, rename the original and save the uploaded file file
                DB = None
                g.db = None
                time.sleep(2) # superstitious waiting
                # rename the current database JSON file a unique name!
                os.rename('./tinydb/flaskpress.json', './tinydb/flaskpress.json.backup.{}'.format(time.time()))
                file.save(pathname)

                # connect to the database again and initialize
                initialize(app)
                generate_meta_info()
            except Exception as e:
                print(e)
                flash("Something went wrong here-- please let administrator know", category="danger")
                raise ValueError("Something went wrong with database upload.")

    return redirect(url_for('admin'))

@app.route('/_admin/user_delete/<user_id>')
@app.route('/_admin/user_delete/<user_id>/<hard_delete>')
@admin_required
def user_delete(user_id, hard_delete=False):
    """ADMIN-ONLY delete a user. A soft delete only sets the is_active to false
    a hard_delete signal deletes the user and reassigns all the pages and files to the current ADMIN
    """
    edit_url = url_for('user_edit', user_id=user_id)
    user_key = {'_id':user_id}
    user = g.db.users.find_one(user_key)
    if user is None:
        flash('No user with id={}'.format(user_id), category="danger")
        return redirect('admin_user')

    if user['username'] != session.get('username'):
        if hard_delete:
            # reassign all pages to admin who is deleting
            pages = g.db.pages.find({'owner':user['username']})
            for page in pages:
                page['owner'] = session.get('username')
                g.db.pages.update_one({'_id':page['_id']}, page)

            g.db.users.remove(user_key)
            flash("User fully deleted, {} pages reassigned to {}.".format(len(pages), g.username), category="primary")
        else:
            user['is_active'] = False
            g.db.users.update_one(user_key, user)
            flash("User deactivated, but still present in database", category="primary")
    else:
        flash("CANNOT DELETE/DEACTIVATE an actively logged in account.", category="danger")

    # redirect to caller or index page if we deleted on an edit view
    if request.referrer == None:
        return redirect(url_for('site', path=None))
    else:
        return redirect(request.referrer)

@app.route('/_admin/pages', methods=('GET','POST'))
@admin_required
def admin_pages():
    """ADMIN-ONLY view to look at all pages.
    TODO: change view to support non-admin users
    """
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )

    # find all pages
    pages = g.db.pages.find()
    return render_template('admin_pages.html', pages=pages)


@app.route('/_admin/file_delete/<file_id>')
@login_required
def file_delete(file_id):
    """LOGIN-REQUIRED view to delete an existing file object and physical file (owned by user)"""
    # currently there is not an accompanying view for regular user role
    file_key = {'_id':file_id}
    f = g.db.files.find_one(file_key)
    if f is None:
        flash("Unable to locate file id={}".format(file_id), category="danger")
        return redirect(url_for('admin_files'))

    pathname = os.path.join(app.config['UPLOAD_FOLDER'], f.get('filepath'))
    if f.get('owner') == session['username'] or session['is_admin']:
        g.db.files.remove(file_key)
        try:
            os.remove(pathname)
            flash('File Successfully Deleted', category="success")
        except:
            flash("Error: problems removing physical file. Check log for details.", category="warning")
    else:
        flash('You are not authorized to remove this file.', category="danger")

    # handle redirect to referer
    if request.referrer == None:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('admin_files'))

@app.route('/_admin/file_edit/<file_id>', methods=['GET','POST'])
@admin_required
def file_edit(file_id):
    """ADMIN-ONLY view to allow edit/delete of a File resource"""
    # handle a search request
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )

    file_key = {'_id':file_id}
    file = g.db.files.find_one(file_key)
    if file is None:
        flash("File with id={} was NOT found".format(file_id), category="danger")

    if request.method == 'POST':
        if file.get('owner')== session['username'] or session['is_admin']:
            title = request.form.get('title')
            if title:
                file['title'] = title
                g.db.files.update_one(file_key, file)
                flash("File information changed", category="success")
                return redirect(url_for('admin_files'))
            else:
                flash('Title must not be blank.', category="warning")
        else:
            flash("You are not authorized to edit/delete this object.", category="danger")

    return render_template('file_edit.html',file=file)


@app.route('/_admin/files')
@admin_required
def admin_files():
    """ADMIN-ONLY view for all File resources
    TODO: change this view to support non-admin users
    """
    # handle search request
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )

    files = g.db.files.find()
    return render_template('admin_files.html', files=files)

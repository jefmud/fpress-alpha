## FlaskPress file handling views
##
## file_upload_handler - allows files to be uploaded
## file_upload - access to uploaded files (better name here?)

from __main__ import app
import datetime
from flask import flash, g, redirect, render_template, request, send_from_directory, url_for
from flask_dropzone import Dropzone
import os
from utils import login_required
from werkzeug.utils import secure_filename

### FILE UPLOADS PARAMETERS
dropzone = Dropzone()
dropzone.init_app(app)

@app.route('/_file/upload', methods=['GET', 'POST'])
@login_required
def file_upload_handler():
    """File upload handling"""
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
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            subfolder = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m/")
            pathname = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)

            # handle name collision if needed
            # filename will add integers at beginning of filename in dotted fashion
            # hello.jpg => 1.hello.jpg => 2.hello.jpg => ...
            # until it finds an unused name
            i=1
            while os.path.isfile(pathname):
                parts = filename.split('.')
                parts.insert(0,str(i))
                filename = '.'.join(parts)
                i += 1
                if i > 100:
                    # probably under attack, so just fail
                    raise ValueError("too many filename collisions, administrator should check this out")

                pathname = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)

            try:
                # ensure directory where we are storing exists, and create it
                directory = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                # finally, save the file AND create its resource object in database
                file.save(pathname)
                
                # put our file reference into the database
                local_filepath = os.path.join(subfolder, filename)
                url = url_for('file_uploads', path=local_filepath)
                file_object = {'title': filename, 'filepath': local_filepath, 'owner': g.username, 'url':url}
                g.db.files.insert(file_object)
                # check if we can find the object
                file_object = g.db.files.find_one(file_object)
                flash("File upload success")
                return redirect(url_for('file_edit', file_id=file_object['_id']))
            except Exception as e:
                print(e)
                flash("Something went wrong here-- please let administrator know", category="danger")
                raise ValueError("Something went wrong with file upload.")

    # TODO, replace with fancier upload drag+drop
    # session['no_csrf'] = True
    return redirect(url_for('admin_files'))


def allowed_file(filename):
    """return True if filename is allowed for upload, False if not allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<path:path>')
def file_uploads(path):
    """serve up a file in our uploads"""
    # should refactor because sloppy use of magic-directory name '/uploads'
    # print("access path={}".format(path))
    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

@app.route('/upload')
@login_required
def file_upload():
    return render_template('upload_file.html')

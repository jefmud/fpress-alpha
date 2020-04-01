#####################
## FlaskPress page views
##
## page_edit - allows a page to be edited by its TinyMongo object id
## page_delete - allows a page to be deleted by its owner.
## search - a generic search for pages returns a search view

from . import app
from . import database
import datetime
from . import details
from flask import abort, flash, g, redirect, render_template, request, session, url_for
from . import forms
from .utils import login_required, slugify, snippet

@app.route('/_page/edit', methods=['GET','POST'])
@app.route('/_page/edit/<id>', methods=['GET','POST'])
@login_required
def page_edit(id=None):
    """edit or create a page"""
    if id is None:
        id = request.args.get('page_id')

    page = g.db.pages.find_one({'_id':id})

    if id:
        # if page id was specified in the url and page does not exist, die 404
        if page is None:
            abort(404)
    else:
        # create a NEW page here
        page = {'owner':g.username}

    if page.get('owner') != g.username and not(g.is_admin):
        # if not authorized to edit the page, flash warn
        flash("You are not the page owner",category="danger")
        return redirect(url_for('site',path=page['slug']))


    form = forms.CSRF() # brings in only the CSRF protection of WTForms

    if form.validate_on_submit():
        # the only validation was that the CSRF token was good
        page['content'] = request.form.get('content')
        page['alt_author'] = request.form.get('alt_author')
        page['title'] = request.form.get('title')
        page['slug'] = request.form.get('slug')
        page['snippet'] = snippet(page['content'])
        page['is_published'] = request.form.get('is_published') == 'on'
        page['show_title'] = request.form.get('show_title') == 'on'
        page['show_nav'] = request.form.get('show_nav') == 'on'
        # Title is in navigation menu
        page['title_nav'] = request.form.get('title_nav') == 'on'
        # page should be treated as a sidebar, this will come into play later
        page['is_sidebar'] = request.form.get('is_sidebar') == 'on'
        # show snippets of featured articles at bottom of content
        page['show_snippets'] = request.form.get('show_snippets') == 'on'

        # this is the basic auxilliary CUSTOM content
        # e.g. a theme would have to support a custom template, for now, lets ignore this
        stylesheet = request.form.get('stylesheet')
        if stylesheet != 'site-default':
            page['stylesheet'] = stylesheet
        else:
            page['stylesheet'] = None

        page['template'] = request.form.get('template')
        page['sidebar_right'] = request.form.get('sidebar_right')
        page['sidebar_left'] = request.form.get('sidebar_left')
        page['footer'] = request.form.get('footer')
        page['categories'] = request.form.get('categories')

        # page time
        if page.get('created_at') is None:
            page['created_at'] = str(datetime.datetime.now())

        page['modified_at'] = str(datetime.datetime.now())


        if not(page['slug']):
            page['slug'] = slugify(page['title'])
        else:
            page['slug'] = page['slug'].strip().strip('/')

        if id:
            # for an existing page, we use update.
            g.db.pages.update_one({'_id':id}, page)
        else:
            # a new page is inserted into collection
            g.db.pages.insert_one(page)

        # in case meta (menus/categories) changed
        database.generate_meta_info()

        flash('Page saved.', category="info")
        # redirecting to a slug is equivalent to a path navigation on the site
        return redirect(url_for('site', path=page.get('slug')))

    # maybe three editors is excessive!
    if g.editor == 'summernote':
        editor_template = 'page_edit_summernote.html'
    elif g.editor == 'tinymce':
        editor_template = 'page_edit_tinymce.html'
    else:
        # default editor, ckeditor
        editor_template = 'page_edit.html'

    return render_template(editor_template, form=form, page=page, id=id, title="Edit page", templates=details.template_mods)


@app.route('/_page/delete/<page_id>')
@login_required
def page_delete(page_id):
    """delete a page by its ID"""
    pquery = {'_id':page_id}
    page = g.db.pages.find_one(pquery)

    if page.get('owner') != g.username and not(g.is_admin):
        # forbidden to edit a page when you are not the owner (admin is ok)
        abort(403)

    if page is None:
        # this particular page ID not in database
        abort(404)

    g.db.pages.delete_many(pquery)

    # move the deleted page into "deleted" collection!
    # need to put in methods to restore the page (TODO)
    g.db.deleted.insert(page)

    # redirect to caller or index page if we deleted on an edit view
    if request.referrer == None:
        return redirect(url_for('site', path=None))
    else:
        return redirect(request.referrer)


@app.route('/search')
def search():
    """search view"""
    search_term = request.args.get('s','')
    # convert query to a list
    pages = list(g.db.pages.find())
    found = []
    for page in pages:
        if not(page.get('is_published')) and not(session.get('is_authenticated')):
            # skip pages that are NOT published and session NOT authenticated.
            continue

        # match pages with content matching search term or title
        if search_term.lower() in page.get('content').lower() \
           or search_term.lower() in page.get('title').lower():
            found.append(page)

    return render_template('search.html', search_term=search_term, pages=found)

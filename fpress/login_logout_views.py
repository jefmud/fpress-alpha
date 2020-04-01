from __main__ import app

from flask import redirect, render_template, url_for, session, flash, g
from forms import UsernamePasswordForm
from werkzeug.security import check_password_hash

@app.route('/login', methods=['GET','POST'])
def login():
    """handle basic login"""
    if g.is_authenticated:
        flash('Please logout first', category='warning')
        return redirect(url_for('site', path=None))

    form = UsernamePasswordForm()
    if form.validate_on_submit():
        # see if user exists
        user = g.db.users.find_one({'username':form.username.data})
        if user:
            if check_password_hash(user.get('password'), form.password.data):
                # inject session data
                session['username'] = form.username.data
                session['is_authenticated'] = True
                if user.get('is_admin'):
                    session['is_admin'] = True

                msg = "Welcome {}!".format(form.username.data)
                flash(msg, category="success")
                return redirect(url_for('site', path=None))

        flash("Incorrect username or password",category="danger")

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out!",category="info")
    return redirect(url_for('site', path=None))

@app.route('/register', methods=['GET','POST'])
def register():
    """register a new user"""
    #form = RegisterForm()
    #if form.validate_on_submit():
        #flash("the data validated", category="success")
    #return render_template('generic_form_ckedit.html', form=form)
    return "Todo"
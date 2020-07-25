from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from pawr.forms import NewPostForm, RegistrationForm, LoginForm
from pawr import app, client, DB_NAME, bc, login_manager, User
from datetime import datetime


@login_manager.user_loader
def load_user(email):
    # find the user by email
    user_in_db = client[DB_NAME].users.find_one({
        'email': email
    })
    # create user object
    user = User()

    if user_in_db:
        user.id = user_in_db['email']
        user.username = user_in_db['username']
        return user
    else:
        return None


# routes start here
@app.route('/')
@app.route('/home')
def home():
    all_posts = client[DB_NAME].posts.find()
    return render_template('home.template.html', posts=all_posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash('You already have an account', 'info')
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username_exist = client[DB_NAME].users.find_one({
            'username': form.username.data
        })
        print(username_exist)
        email_exist = client[DB_NAME].users.find_one({
            'email': form.email.data

        })
        if username_exist:
            flash('Username already taken, please choose another one', 'danger')
        elif email_exist:
            flash('Email already registered, please log in', 'danger')
        else:
            client[DB_NAME].users.insert_one({
                'username': form.username.data,
                'email': form.email.data,
                'password': bc.generate_password_hash(form.password.data).decode('utf-8'),
            })
            flash('Your account has been created, please log in', "success")
            return redirect(url_for('login'))
    return render_template('register.template.html',
                           form=form, title='Sign Up')


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user_in_db = client[DB_NAME].users.find_one({
            'email': form.email.data
        })
        if user_in_db:
            user = User()
            user.id = user_in_db['email']
            if bc.check_password_hash(user_in_db['password'], form.password.data):
                login_user(user, remember=form.remember.data)
                flash("Successfully Logged In", "success")
                return redirect(url_for('home'))
            else:
                flash('Login failed, please check username and password',
                      'danger')
        else:
            flash('User not found', 'danger')
    return render_template('login.template.html',
                           form=form, title='Login')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/post/new', methods=["GET", "POST"])
@login_required
def new_post():
    form = NewPostForm()
    if form.validate_on_submit():
        client[DB_NAME].posts.insert_one({
            'title': form.title.data,
            'content': form.content.data,
            'datetime_posted': datetime.now().replace(microsecond=0),
            'author': {
                'email': current_user.id,
                'username': current_user.username
            },
        })
        flash(f"New post '{form.title.data}' created", "success")
        return redirect(url_for('home'))
    return render_template('new_post.template.html',
                           title='New Post', form=form)

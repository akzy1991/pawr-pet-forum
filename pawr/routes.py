from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from pawr.forms import QuestionForm, RegistrationForm, LoginForm
from pawr import app, client, DB_NAME, bc, login_manager, User
from bson.objectid import ObjectId
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
    all_questions = client[DB_NAME].questions.find()
    return render_template('home.template.html', questions=all_questions, title='home')


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
            flash('Username already taken, please choose another one',
                  'danger')
        elif email_exist:
            flash('Email already registered, please log in', 'danger')
        else:
            password = bc.generate_password_hash(form.password.data)
            client[DB_NAME].users.insert_one({
                'username': form.username.data,
                'email': form.email.data,
                'password': password.decode('utf-8'),
            })
            flash('Your account has been created, please log in', "success")
            return redirect(url_for('login'))
    return render_template('register.template.html',
                           form=form, title='Sign Up')


@app.route('/account')
@login_required
def account():
    return render_template('account.template.html', title='account')


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
            if bc.check_password_hash(user_in_db['password'],
                                      form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash("Successfully Logged In", "success")
                return redirect(next_page) if next_page else redirect(url_for('home'))
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


@app.route('/question/new', methods=["GET", "POST"])
@login_required
def new_question():
    form = QuestionForm()
    if form.validate_on_submit():
        client[DB_NAME].questions.insert_one({
            'question': form.question.data,
            'datetime_posted': datetime.now().replace(microsecond=0),
            'author': {
                'email': current_user.id,
                'username': current_user.username
            },
        })
        flash("Question posted", "success")
        return redirect(url_for('home'))
    return render_template('question.template.html',
                           title='New Question',
                           header='New Question', form=form)


@app.route('/question/edit/<question_id>', methods=["GET", "POST"])
@login_required
def edit_question(question_id):
    question = client[DB_NAME].questions.find_one({
        "_id": ObjectId(question_id)
    })
    if question['author']['username'] != current_user.username:
        abort(403)
    form = QuestionForm()
    if form.validate_on_submit():
        updated_question = form.question.data
        print(updated_question)
        client[DB_NAME].questions.update_one({
            "_id": ObjectId(question_id)
        }, {
            "$set": {
                "hello": 'hello',
                "question": updated_question
            }
        })
        return redirect(url_for('home'))
    form.question.data = question['question']
    return render_template('question.template.html',
                           title='Edit Question',
                           header='Edit Question', form=form)

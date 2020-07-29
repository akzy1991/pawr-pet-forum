from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from pawr.forms import QuestionForm, RegistrationForm, LoginForm, AnswerForm
from pawr import app, client, DB_NAME, bc, login_manager, User, pymongo
from bson.objectid import ObjectId
from datetime import datetime


# code to humanize time taken from
# https://shubhamjain.co/til/how-to-render-human-readable-time-in-jinja/
def humanize_ts(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(int(second_diff)) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"


app.jinja_env.filters['humanize'] = humanize_ts


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
    # search bar
    search_terms = request.args.get('search-terms')
    criteria = {}
    if search_terms != '' and search_terms is not None:
        criteria['question'] = {
            '$regex': search_terms,
            '$options': "i"
        }
    print(criteria)
    questions = client[DB_NAME].questions.find(criteria)
    questions.sort('datetime_posted', pymongo.DESCENDING)
    return render_template('home.template.html',
                           questions=questions, title='home')


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
    flash('You are now logged out', 'success')
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
        flash('You are not authorized to view this page')
        return redirect(url_for('home'))
    form = QuestionForm()
    if form.validate_on_submit():
        updated_question = form.question.data
        print(updated_question)
        client[DB_NAME].questions.update_one({
            "_id": ObjectId(question_id)
        }, {
            "$set": {
                "question": updated_question
            }
        })
        return redirect(url_for('home'))
    form.question.data = question['question']
    return render_template('question.template.html',
                           title='Edit Question',
                           header='Edit Question', form=form)


@app.route('/question/delete/<question_id>', methods=["POST"])
@login_required
def confirm_delete(question_id):
    question = client[DB_NAME].questions.find_one({
        "_id": ObjectId(question_id)
    })
    if question['author']['username'] != current_user.username:
        abort(403)
    client[DB_NAME].questions.remove({
        "_id": ObjectId(question_id)
    })
    return redirect(url_for('home'))


@app.route('/question/answer/<question_id>', methods=["GET", "POST"])
@login_required
def answer_question(question_id):
    question = client[DB_NAME].questions.find_one({
        "_id": ObjectId(question_id)
    })
    form = AnswerForm()
    if form.validate_on_submit():
        client[DB_NAME].questions.update_one({
            "_id": ObjectId(question_id),
        }, {
            "$push": {
                'answers': {
                    # ObjectId() is a function that returns a new ObjectId
                    "_id": ObjectId(),
                    "answer": form.answer.data,
                    "datetime_posted": datetime.now().replace(microsecond=0),
                    "author": {
                        'email': current_user.id,
                        'username': current_user.username
                    }
                }
            }
        })
        flash('Answer successfully submitted', 'success')
        return redirect(url_for('home'))
    return render_template('answer.template.html',
                           title='Answer',
                           header=f"Q: {question['question']}",
                           question=question,
                           form=form)


@app.route('/question/answer/delete/<answer_id>', methods=["POST"])
@login_required
def confirm_delete_answer(answer_id):
    answer_to_delete = client[DB_NAME].questions.find_one({
        'answers._id': ObjectId(answer_id)
    }, {
        'answers': {
            '$elemMatch': {
                '_id': ObjectId(answer_id)
            }
        }
    })['answers'][0]
    if answer_to_delete['author']['username'] != current_user.username:
        abort(403)
        flash('You are not authorized to view this page')
        return redirect(url_for('home'))
    client[DB_NAME].questions.update_one({
        'answers._id': ObjectId(answer_id)
    }, {
        "$pull": {
            'answers': {
                '_id': ObjectId(answer_id)
            }
        }
    })
    flash('Answer successfully deleted', 'success')
    return redirect(url_for('home'))


@app.route('/question/answer/edit/<answer_id>', methods=["GET", "POST"])
@login_required
def edit_answer(answer_id):
    answer_to_delete = client[DB_NAME].questions.find_one({
        'answers._id': ObjectId(answer_id)
    }, {
        'answers': {
            '$elemMatch': {
                '_id': ObjectId(answer_id)
            }
        }
    })['answers'][0]
    question = client[DB_NAME].questions.find_one({
        'answers._id': ObjectId(answer_id)
    })

    if answer_to_delete['author']['username'] != current_user.username:
        abort(403)
        flash('You are not authorized to view this page')
        return redirect(url_for('home'))

    form = AnswerForm()
    if form.validate_on_submit():
        updated_answer = form.answer.data
        client[DB_NAME].questions.update_one({
            'answers._id': ObjectId(answer_id)
        }, {
            "$set": {
                'answers.$.answer': updated_answer,
            }
        })
        flash('Answer successfully edited', 'success')
        return redirect(url_for('home'))
    form.answer.data = answer_to_delete['answer']
    return render_template('answer.template.html',
                           title='Edit Answer',
                           header=f"Q: {question['question']}", form=form)

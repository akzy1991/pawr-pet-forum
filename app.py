from flask import Flask, render_template, request, redirect, url_for, flash
import pymongo
from dotenv import load_dotenv
from forms import NewPostForm, RegistrationForm, LoginForm
from bson import ObjectId
import os
from datetime import datetime

# load env
load_dotenv()

app = Flask(__name__)

# connect to mongo
MONGO_URI = os.environ.get('MONGO_URI')
client = pymongo.MongoClient(MONGO_URI)

# define my db_name
DB_NAME = "pawr"

# read in the SESSION_KEY variable from the operating system environment
SESSION_KEY = os.environ.get('SESSION_KEY')

# set the session key
app.secret_key = SESSION_KEY


# routes start here
@app.route('/')
@app.route('/home')
def home():
    all_posts = client[DB_NAME].posts.find()
    return render_template('home.template.html', posts=all_posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash("Account Created", "success")
        return redirect(url_for('home'))
    return render_template('register.template.html',
                           form=form, title='Sign Up')


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash("Successfully Logged In", "success")
        return redirect(url_for('home'))
    else:
        flash('Login failed, please check username and password', 'danger')
    return render_template('login.template.html',
                           form=form, title='Login')


@app.route('/post/create', methods=["GET", "POST"])
def new_post():
    form = NewPostForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        date_time = datetime.now().replace(microsecond=0)
        client[DB_NAME].posts.insert_one({
            'title': title,
            'content': content,
            'datetime_posted': date_time
        })
        flash(f"New post '{form.title.data}' created", "success")
        return redirect(url_for('home'))
    return render_template('new_post.template.html',
                           title='New Post', form=form)


# "magic code" -- boilerplate
if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)

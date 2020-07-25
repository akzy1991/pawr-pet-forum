from flask import Flask
import pymongo
from flask_login import UserMixin, LoginManager
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
import os


# load env
load_dotenv()

app = Flask(__name__)

# connect to mongodb
MONGO_URI = os.environ.get('MONGO_URI')
client = pymongo.MongoClient(MONGO_URI)


# define my db_name
DB_NAME = "pawr"

# read in the SESSION_KEY variable from the operating system environment
SESSION_KEY = os.environ.get('SESSION_KEY')
app.secret_key = SESSION_KEY


# login manager
login_manager = LoginManager()
login_manager.init_app(app)

# password encryption
bc = Bcrypt(app)


# create user object
class User(UserMixin):
    pass

# prevent circular import
from pawr import routes

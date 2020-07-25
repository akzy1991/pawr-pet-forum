from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from pawr import client, DB_NAME


class QuestionForm(FlaskForm):
    question = TextAreaField('Question', validators=[DataRequired(),
                                                     Length(min=2, max=500)])
    submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class AnswerForm(FlaskForm):
    answer = TextAreaField('Content', validators=[DataRequired(),
                                                  Length(min=2, max=500)])
    submit = SubmitField('Submit Answer')

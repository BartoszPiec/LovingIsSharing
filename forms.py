from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')



class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class LinkFlatmateForm(FlaskForm):
    link_code = StringField('Link Code', validators=[DataRequired()])
    submit = SubmitField('Link Flatmate')


class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description')
    assigned_to = SelectField('Assign To', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Task')


class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    email = EmailField('Your Email', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

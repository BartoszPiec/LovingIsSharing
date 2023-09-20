from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from random import choice
from sqlalchemy import ForeignKey, Table, Integer, Column
from sqlalchemy.orm import relationship
from flask import jsonify
import string
import forms
import smtplib
from email.message import EmailMessage
import os



EMAIL_PASSWORD = "bildznatuvlybkne"
EMAIL_ADDRESS = "lovingissharingcontact@gmail.com"


app = Flask(__name__)
Bootstrap5(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Users.db"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


# Many-to-Many Association Table
flatmate_link = Table(
    'flatmate_link', db.metadata,
    Column('user_id', Integer, ForeignKey('User.id'), primary_key=True),
    Column('flatmate_id', Integer, ForeignKey('User.id'), primary_key=True)
                      )


# User class
class User(UserMixin, db.Model):

    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    link_code = db.Column(db.String(10), unique=True, nullable=False)

    def generate_link_code(self):
        self.link_code = ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(10))

    shared_flatmates = relationship(
        "User",
        secondary=flatmate_link,
        primaryjoin=id == flatmate_link.c.user_id,
        secondaryjoin=id == flatmate_link.c.flatmate_id,
        backref="flatmates",
    )


class FlatmateTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('User.id'))
    done = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()



@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def home():

    return render_template('index.html')


# Register route
@app.route('/register', methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect('/')

    register_form = forms.RegistrationForm()

    if register_form.validate_on_submit():
        # Checking is user exist in database
        result = db.session.execute(db.select(User).where(User.email == register_form.email.data))
        user = result.scalar()

        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        # If not we update our database with new User
        else:

            passw = generate_password_hash(password=register_form.password.data, method="pbkdf2:sha256", salt_length=8)

            new_user = User(
                email=register_form.email.data,
                password_hash=passw,
                username=register_form.username.data
            )
            new_user.generate_link_code()
            db.session.add(new_user)
            db.session.commit()

            # After creating new user we instantly redirect him to main page
            login_user(new_user)
            flash('Registration successful!')
            return redirect('/')
    return render_template('register.html', form=register_form)


# Loging in route
@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect('/main')

    login_form = forms.LoginForm()

    if login_form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == login_form.email.data))
        user = result.scalar()

        if user:
            password_hash = user.password_hash
            if check_password_hash(pwhash=password_hash, password=login_form.password.data):
                login_user(user)
                flash('Logged in successfully!')
                return redirect('/main')
            else:
                flash("Wrong password, please try again.")
        else:
            flash("User with this email address does not exist.")
    return render_template("login.html", form=login_form)


@app.route('/main')
@login_required
def main():
    # Get the current user's flatmates
    user_flatmates = current_user.shared_flatmates

    # Include the current user in the list of flatmates
    all_flatmates = user_flatmates + [current_user]


    # Get tasks assigned to the current user and their flatmates
    tasks = FlatmateTask.query.filter(FlatmateTask.assigned_to.in_([user.id for user in all_flatmates])).all()

    tasks_data = []

    for task in tasks:
        assigned_user = db.session.get(User, task.assigned_to)
        task_info = {
            'title': task.title,
            'description': task.description,
            'assigned_to': assigned_user.username if assigned_user else 'Unassigned',
            'done': task.done,
            'id': task.id
        }
        tasks_data.append(task_info)

    # Using TaskForm to add a new task

    task_form = forms.TaskForm()
    user_choices = [(flatmate.id, flatmate.username) for flatmate in all_flatmates]
    task_form.assigned_to.choices = user_choices

    # Using the form to pass it for linking users

    link_form = forms.LinkFlatmateForm()

    return render_template('main.html', flatmates=user_flatmates, task_data=tasks_data, form=task_form,
                           link_form=link_form)


@app.route('/link_flatmate', methods=["POST"])
@login_required
def link_flatmate():
    link_form = forms.LinkFlatmateForm()

    if link_form.validate_on_submit():
        flatmate = db.session.execute(db.select(User).where(User.link_code == link_form.link_code.data)).scalar()

        if flatmate in current_user.shared_flatmates:
            flash("You are both already linked together!")

        elif flatmate:
            # Add the flatmate to the shared_flatmates relationship
            current_user.shared_flatmates.append(flatmate)
            db.session.commit()
            flash(f'Successfully linked with {flatmate.username}!')

        else:
            print("User does not exist")
            flash('User does not exist.')

    return redirect('/main')


@app.route('/add_task', methods=['POST'])
@login_required
def add_task():


    form = forms.TaskForm()


    user_flatmates = current_user.shared_flatmates
    print(user_flatmates)
    user_choices = [(flatmate.id, flatmate.username) for flatmate in user_flatmates]
    user_choices.append((current_user.id, current_user.username))
    form.assigned_to.choices = user_choices

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        assigned_to_id = form.assigned_to.data
        print("good")

        task = FlatmateTask(title=title, description=description, assigned_to=assigned_to_id)
        db.session.add(task)
        db.session.commit()
        print("success")
    flash('Task added successfully!')
    return redirect('/main')


@app.route('/mark_done/<int:task_id>', methods=['POST'])
@login_required
def mark_done(task_id):
    task = db.session.get(FlatmateTask, task_id)

    if not task:
        return jsonify({'success': False, 'error': 'Task not found'})

    if task.assigned_to != current_user.id:
        if task.title == "Cook dinner":
            # Logic for handling the "making dinner" task
            dishes_task = FlatmateTask.query.filter_by(title="Wash dishes", assigned_to=current_user.id).first()
            if dishes_task:
                return jsonify({'success': False, 'error': 'You must first complete "Wash dishes" task.'})

        return jsonify({'success': False, 'error': "Sorry that's not your task"})  # Updated error message

    task.done = not task.done
    db.session.commit()  # Commit the changes to the database

    return jsonify({'success': True, 'task_done': task.done})


@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = db.session.get(FlatmateTask, task_id)

    if not task:
        flash('Task not found.')
    elif task.assigned_to != current_user.id:
        flash("You can't delete tasks assigned to other users.")
    else:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully.')

    return redirect('/main')


@app.route('/FAQs')
def faq_page():

    return render_template("FAQs.html")

@app.route('/features')
def features():
    return render_template('features.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = forms.ContactForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        subject = form.subject.data
        message = form.message.data

        try:
            # Create an EmailMessage object
            msg = EmailMessage()
            msg.set_content(f"Name: {name}\nEmail: {email}\n\n{message}")
            msg['Subject'] = subject
            msg['From'] = EMAIL_ADDRESS  # Your email address
            msg['To'] = EMAIL_ADDRESS  # Recipient's email address

            # Connect to the SMTP server (e.g., Gmail)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Your email credentials

            # Send the email
            server.send_message(msg)
            server.quit()

            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))

        except Exception as e:
            flash('An error occurred while sending your message. Please try again later.', 'danger')
            return redirect(url_for('contact'))

    return render_template('contact.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)

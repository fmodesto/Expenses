import uuid
import urllib
from datetime import date
from decimal import Decimal

from flask.ext.login import login_required, UserMixin, current_user, LoginManager, login_user, logout_user
from flask.helpers import send_from_directory, flash
import os
from flask import Flask, render_template, url_for, redirect, request
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import DecimalField, SelectField, DateField, SubmitField, HiddenField, StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email
from wtforms.widgets.html5 import NumberInput, DateInput


TWOPLACES = Decimal(10) ** -2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SECRET_KEY'] = os.getenv('EXPENSES_KEY', 's3cret')
app.config['EXPENSES_UPLOAD'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'uploads')
app.config['EXPENSES_CURRENCY'] = [('GBR', 'GBP'), ('EUR', 'EUR')]
app.config['EXPENSES_CONCEPT'] = [('MEALS', 'Meals'), ('TRANSPORT', 'Transport'), ('ACCOMODATION', 'Accomodation'), ('FLIGHTS', 'Flights'),
                                  ('CAR_RENTAL', 'Car Rental'), ('OTHER', 'Other')]

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'
login_manager.login_message = None


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class ExpenseForm(Form):
    image = HiddenField()
    price = DecimalField(widget=NumberInput())
    currency = SelectField(choices=app.config['EXPENSES_CURRENCY'])
    concept = SelectField(choices=app.config['EXPENSES_CONCEPT'])
    date = DateField(validators=[DataRequired()], widget=DateInput())
    submit = SubmitField('Submit')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    expenses = db.relationship('Expense')


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Text, nullable=False)
    currency = db.Column(db.Enum('GBR', 'EUR'), nullable=False)
    concept = db.Column(db.Enum('MEALS', 'ACCOMODATION', 'TRANSPORT', 'FLIGHTS', 'CAR_RENTAL', 'OTHER'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    attachment = db.Column(db.Text)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    return render_template('index.html', expenses=current_user.expenses)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and verify_password(form.password.data, user.password):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ExpenseForm(date=date.today())
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = str(uuid.uuid4())
            urllib.urlretrieve(form.image.data, os.path.join(app.config['EXPENSES_UPLOAD'], filename))

        db.session.add(Expense(
            user=current_user.id,
            price=str(form.price.data.quantize(TWOPLACES)),
            currency=form.currency.data,
            concept=form.concept.data,
            date=form.date.data,
            attachment=filename))
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html', form=form)


@app.route('/uploads/<image>')
def uploads(image):
    return send_from_directory(app.config['EXPENSES_UPLOAD'], image)


if __name__ == '__main__':
    app.debug = True
    app.run()
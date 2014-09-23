import os
import uuid
import urllib
from datetime import date
from decimal import Decimal
from flask import Flask, render_template, url_for, redirect, session
from flask.ext.bootstrap import Bootstrap
from flask.ext.openid import OpenID, COMMON_PROVIDERS
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import DecimalField, SelectField, DateField, SubmitField, HiddenField
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput, DateInput


TWOPLACES = Decimal(10) ** -2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SECRET_KEY'] = os.getenv('EXPENSES_KEY', 's3cret')
app.config['EXPENSES_UPLOAD'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'uploads')
app.config['EXPENSES_OID'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'oid')
app.config['EXPENSES_CURRENCY'] = [('GBR', 'GBP'), ('EUR', 'EUR')]
app.config['EXPENSES_CONCEPT'] = [('MEALS', 'Meals'), ('TRANSPORT', 'Transport'), ('ACCOMODATION', 'Accomodation'), ('FLIGHTS', 'Flights'),
                                  ('CAR_RENTAL', 'Car Rental'), ('OTHER', 'Other')]

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
oid = OpenID(app, app.config['EXPENSES_OID'], safe_roots=[])


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Text, nullable=False)
    price = db.Column(db.Text, nullable=False)
    currency = db.Column(db.Enum('GBR', 'EUR'), nullable=False)
    concept = db.Column(db.Enum('MEALS', 'ACCOMODATION', 'TRANSPORT', 'FLIGHTS', 'CAR_RENTAL', 'OTHER'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    attachment = db.Column(db.Binary, )


class ExpenseForm(Form):
    image = HiddenField()
    price = DecimalField(widget=NumberInput())
    currency = SelectField(choices=app.config['EXPENSES_CURRENCY'])
    concept = SelectField(choices=app.config['EXPENSES_CONCEPT'])
    date = DateField(validators=[DataRequired()], widget=DateInput())
    submit = SubmitField('Submit')


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    expenses = Expense.query.all()
    return render_template('index.html', expenses=expenses)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session:
        return redirect(url_for('login'))

    form = ExpenseForm(date=date.today())
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = str(uuid.uuid4())
            urllib.urlretrieve(form.image.data, os.path.join(app.config['EXPENSES_UPLOAD'], filename))

        expense = Expense(
            user=session['user'],
            price=str(form.price.data.quantize(TWOPLACES)),
            currency=form.currency.data,
            concept=form.concept.data,
            date=form.date.data,
            attachment=filename)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if 'user' in session:
        return redirect(oid.get_next_url())
    return oid.try_login(COMMON_PROVIDERS['google'], ask_for=['email'])


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(oid.get_next_url())


@oid.after_login
def login(resp):
    session['user'] = resp.email
    return redirect(oid.get_next_url())


if __name__ == '__main__':
    app.debug = True
    app.run(static_files={'/uploads': app.config['EXPENSES_UPLOAD']})

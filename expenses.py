from flask.helpers import send_from_directory
import os
import uuid
import urllib
from datetime import date
from decimal import Decimal
from flask import Flask, render_template, url_for, redirect
from flask.ext.bootstrap import Bootstrap
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
app.config['EXPENSES_CURRENCY'] = [('GBR', 'GBP'), ('EUR', 'EUR')]
app.config['EXPENSES_CONCEPT'] = [('MEALS', 'Meals'), ('TRANSPORT', 'Transport'), ('ACCOMODATION', 'Accomodation'), ('FLIGHTS', 'Flights'),
                                  ('CAR_RENTAL', 'Car Rental'), ('OTHER', 'Other')]

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
    expenses = Expense.query.all()
    return render_template('index.html', expenses=expenses)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = ExpenseForm(date=date.today())
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = str(uuid.uuid4())
            urllib.urlretrieve(form.image.data, os.path.join(app.config['EXPENSES_UPLOAD'], filename))

        expense = Expense(
            price=str(form.price.data.quantize(TWOPLACES)),
            currency=form.currency.data,
            concept=form.concept.data,
            date=form.date.data,
            attachment=filename)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html', form=form)


@app.route('/uploads/<image>')
def uploads(image):
    print 'llego'
    return send_from_directory(app.config['EXPENSES_UPLOAD'], image)


if __name__ == '__main__':
    app.debug = True
    app.run()

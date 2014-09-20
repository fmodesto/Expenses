import uuid
import os
from flask import Flask, render_template, url_for, redirect
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import FileField, DecimalField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets.html5 import NumberInput, DateInput
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SECRET_KEY'] = '\x0f\xa8\x15\x83\xa46G\xcd\x9d\xa2\xd88\xa4\xde\xe7^`:6C\x8c\x8c\xb3\x0c'
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
    attachment = db.Column(db.Text)


class ExpenseForm(Form):
    upload = FileField(validators=[DataRequired()])
    price = DecimalField(widget=NumberInput())
    currency = SelectField(choices=app.config['EXPENSES_CURRENCY'])
    concept = SelectField(choices=app.config['EXPENSES_CONCEPT'])
    date = DateField(validators=[DataRequired()], default=date.today(), widget=DateInput())
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ExpenseForm()

    if form.validate_on_submit():
        file = None
        if form.upload.data:
            file = str(uuid.uuid4())
            form.upload.data.save(os.path.join(app.config['EXPENSES_UPLOAD'], file))

        expense = Expense(
            price=str(form.price.data),
            currency=form.currency.data,
            concept=form.concept.data,
            date=form.date.data,
            attachment=file)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html', form=form)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

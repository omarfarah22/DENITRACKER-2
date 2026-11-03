from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    debts = db.relationship('Debt', backref='customer', lazy=True)

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    customers = Customer.query.all()
    total_deni = db.session.query(db.func.sum(Debt.amount)).filter_by(is_paid=False).scalar() or 0
    return render_template('index.html', customers=customers, total_deni=total_deni)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        new_customer = Customer(name=request.form['name'], phone=request.form['phone'])
        db.session.add(new_customer)
        db.session.commit()
        return redirect('/')
    return render_template('add_customer.html')

@app.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    unpaid = Debt.query.filter_by(customer_id=customer_id, is_paid=False).all()
    total = sum([d.amount for d in unpaid])
    return render_template('customer_detail.html', customer=customer, debts=unpaid, total=total)

@app.route('/add_debt/<int:customer_id>', methods=['POST'])
def add_debt(customer_id):
    amount = float(request.form['amount'])
    desc = request.form['description']
    debt = Debt(customer_id=customer_id, amount=amount, description=desc)
    db.session.add(debt)
    db.session.commit()
    return redirect(url_for('customer_detail', customer_id=customer_id))

@app.route('/pay_debt/<int:debt_id>')
def pay_debt(debt_id):
    debt = Debt.query.get_or_404(debt_id)
    debt.is_paid = True
    db.session.commit()
    return redirect(url_for('customer_detail', customer_id=debt.customer_id))

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
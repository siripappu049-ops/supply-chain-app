from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Shipment, Inventory
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shiptrackpro-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shiptrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    shipments = Shipment.query.all()
    total = len(shipments)
    in_transit = len([s for s in shipments if s.status == 'In Transit'])
    delivered = len([s for s in shipments if s.status == 'Delivered'])
    pending = len([s for s in shipments if s.status == 'Pending'])

    # Chart data
    status_labels = ['Pending', 'In Transit', 'Delivered']
    status_values = [pending, in_transit, delivered]

    recent_shipments = Shipment.query.order_by(Shipment.id.desc()).limit(5).all()

    return render_template('dashboard.html',
        total=total, in_transit=in_transit,
        delivered=delivered, pending=pending,
        status_labels=json.dumps(status_labels),
        status_values=json.dumps(status_values),
        recent_shipments=recent_shipments
    )

@app.route('/inventory')
@login_required
def inventory():
    items = Inventory.query.all()
    shipments = Shipment.query.order_by(Shipment.id.desc()).all()
    return render_template('inventory.html', items=items, shipments=shipments)

@app.route('/add_shipment', methods=['POST'])
@login_required
def add_shipment():
    shipment = Shipment(
        tracking_number=request.form.get('tracking_number'),
        origin=request.form.get('origin'),
        destination=request.form.get('destination'),
        status=request.form.get('status'),
        carrier=request.form.get('carrier'),
        date=datetime.now().strftime('%Y-%m-%d')
    )
    db.session.add(shipment)
    db.session.commit()
    flash('Shipment added successfully!')
    return redirect(url_for('inventory'))

@app.route('/add_inventory', methods=['POST'])
@login_required
def add_inventory():
    item = Inventory(
        name=request.form.get('name'),
        sku=request.form.get('sku'),
        quantity=int(request.form.get('quantity')),
        warehouse=request.form.get('warehouse'),
        category=request.form.get('category')
    )
    db.session.add(item)
    db.session.commit()
    flash('Inventory item added!')
    return redirect(url_for('inventory'))

@app.route('/delete_shipment/<int:id>')
@login_required
def delete_shipment(id):
    s = Shipment.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/delete_inventory/<int:id>')
@login_required
def delete_inventory(id):
    item = Inventory.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory'))

def seed_data():
    if User.query.count() == 0:
        admin = User(username='admin', email='admin@shiptrack.com')
        admin.set_password('admin123')
        db.session.add(admin)

    if Shipment.query.count() == 0:
        shipments = [
            Shipment(tracking_number='STP-001', origin='New York', destination='Los Angeles', status='Delivered', carrier='FedEx', date='2024-03-01'),
            Shipment(tracking_number='STP-002', origin='Chicago', destination='Houston', status='In Transit', carrier='UPS', date='2024-03-05'),
            Shipment(tracking_number='STP-003', origin='Miami', destination='Seattle', status='Pending', carrier='DHL', date='2024-03-08'),
            Shipment(tracking_number='STP-004', origin='Boston', destination='Denver', status='In Transit', carrier='FedEx', date='2024-03-09'),
            Shipment(tracking_number='STP-005', origin='Atlanta', destination='Phoenix', status='Delivered', carrier='UPS', date='2024-03-10'),
        ]
        db.session.add_all(shipments)

    if Inventory.query.count() == 0:
        items = [
            Inventory(name='Industrial Sensors', sku='INS-001', quantity=150, warehouse='Warehouse A', category='Electronics'),
            Inventory(name='Steel Pipes', sku='STP-201', quantity=320, warehouse='Warehouse B', category='Materials'),
            Inventory(name='Safety Helmets', sku='SFH-034', quantity=75, warehouse='Warehouse A', category='Safety'),
            Inventory(name='Conveyor Belts', sku='CVB-112', quantity=20, warehouse='Warehouse C', category='Equipment'),
            Inventory(name='Packing Boxes', sku='PKB-500', quantity=1200, warehouse='Warehouse B', category='Packaging'),
        ]
        db.session.add_all(items)

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)

import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Product, Category, Order, OrderItem
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sabari-enterprise-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sabari.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize Database and Default Super Admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        super_admin = User(username='admin', password=hashed_password, role='Super Admin')
        db.session.add(super_admin)
        db.session.commit()
        print("Default Super Admin created: admin / admin123")


# ==========================================
# ADMIN AUTHENTICATION ROUTES
# ==========================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # Only allow Admin roles in the backend
            if user.role in ['Super Admin', 'Product Manager', 'Sales Manager', 'Inventory Manager', 'Content Manager']:
                login_user(user, remember=remember)
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Access denied: You do not have admin privileges.', 'danger')
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
            
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

# ==========================================
# ADMIN DASHBOARD ROUTES
# ==========================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Gather stats for the dashboard
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(role='Customer').count()
    return render_template('admin/dashboard.html', 
                           total_products=total_products,
                           total_orders=total_orders,
                           total_customers=total_customers)

# ==========================================
# PUBLIC API ROUTES (For index.html)
# ==========================================

contact_requests = []
custom_requests = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    # For Phase 1, if the DB is empty, we return a mock list so the frontend doesn't break
    products = Product.query.all()
    if not products:
        # Fallback mock data
        return jsonify([
            { 'id': 1, 'name': 'Separating Funnel Pear Shape', 'cat': 'funnel', 'price': 1250, 'caps': ['250ml', '500ml'], 'meta': 'Pear shape · PTFE stopcock', 'desc': 'High quality borosilicate glass.' },
            { 'id': 2, 'name': 'Borosilicate Beaker Low Form', 'cat': 'beaker', 'price': 360, 'caps': ['100ml', '250ml'], 'meta': 'Low form · graduated', 'desc': 'Griffin low-form beakers.' }
        ]), 200
    
    product_list = []
    for p in products:
        product_list.append({
            'id': p.id,
            'name': p.name,
            'cat': p.category.name if p.category else 'uncategorized',
            'price': p.price,
            'caps': ['Default'], # To be expanded in Phase 2
            'meta': p.short_description,
            'desc': p.description
        })
    return jsonify(product_list), 200

@app.route('/api/checkout', methods=['POST'])
def handle_checkout():
    data = request.json
    cart = data.get('cart', [])
    user_info = data.get('userInfo', {})
    
    order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
    
    # Calculate total
    total = sum(item.get('qty', 1) * 100 for item in cart) # Mock price calc for now
    
    new_order = Order(
        id=order_id,
        customer_name=user_info.get('name', 'Guest'),
        customer_email=user_info.get('email', ''),
        customer_address=user_info.get('address', ''),
        total_amount=total
    )
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'message': 'Order placed successfully!'
    }), 200

@app.route('/api/track_order/<order_id>', methods=['GET'])
def track_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
        
    return jsonify({
        'order_id': order.id,
        'status': order.status,
        'items_count': 0
    }), 200

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.json
    contact_requests.append(data)
    return jsonify({'success': True, 'message': 'Message sent!'}), 200

@app.route('/api/custom', methods=['POST'])
def handle_custom():
    data = request.json
    custom_requests.append(data)
    return jsonify({'success': True, 'message': 'Custom request submitted!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

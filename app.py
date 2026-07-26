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
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(role='Customer').count()
    return render_template('admin/dashboard.html', 
                           total_products=total_products,
                           total_orders=total_orders,
                           total_customers=total_customers)

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            new_cat = Category(name=name, description=request.form.get('description'))
            db.session.add(new_cat)
            db.session.commit()
            flash('Category added!', 'success')
        return redirect(url_for('admin_categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted!', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if request.method == 'POST':
        new_prod = Product(
            sku=request.form.get('sku'),
            name=request.form.get('name'),
            category_id=request.form.get('category_id'),
            price=request.form.get('price'),
            capacities=request.form.get('capacities'),
            short_description=request.form.get('short_description'),
            description=request.form.get('description'),
            stock_quantity=request.form.get('stock_quantity')
        )
        db.session.add(new_prod)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('admin_products'))
        
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    prod = Product.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    flash('Product deleted!', 'success')
    return redirect(url_for('admin_products'))

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
    products = Product.query.all()
    if not products:
        return jsonify([
            { 'id': 1, 'name': 'Separating Funnel Pear Shape', 'cat': 'funnel', 'price': 1250, 'caps': ['250ml', '500ml'], 'meta': 'Pear shape · PTFE stopcock', 'desc': 'High quality borosilicate glass.' }
        ]), 200
    
    product_list = []
    for p in products:
        caps_array = [c.strip() for c in p.capacities.split(',')] if p.capacities else ['Default']
        product_list.append({
            'id': p.id,
            'name': p.name,
            'cat': p.category.name.lower() if p.category else 'uncategorized',
            'price': p.price,
            'caps': caps_array,
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

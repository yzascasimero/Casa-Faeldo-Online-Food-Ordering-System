# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Admin, Customer, Product, Order, OrderItem, Reservation
from sqlalchemy import inspect, text
from datetime import datetime, date, time, timedelta
from collections import defaultdict

# --- Business Hours Helper Functions ---
def is_weekend(check_date):
    """Check if the given date is a weekend (Saturday or Sunday)"""
    return check_date.weekday() >= 5

def get_business_hours(check_date):
    """Get opening and closing hours for a given date"""
    if is_weekend(check_date):
        opening_hour = 10  # 10 AM for weekends
    else:
        opening_hour = 11  # 11 AM for weekdays
    closing_hour = 21  # 9 PM for all days
    
    return opening_hour, closing_hour

def is_within_business_hours(check_datetime):
    """Check if the given datetime is within business hours"""
    opening_hour, closing_hour = get_business_hours(check_datetime.date())
    
    # Convert check_datetime to UTC+8
    current_hour = check_datetime.hour
    
    return opening_hour <= current_hour < closing_hour

# --- App Initialization ---
app = Flask(__name__)
app.config.from_object(Config)
app.config.setdefault('UPLOAD_FOLDER', os.path.join('static', 'uploads'))
app.config.setdefault('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not session.get('is_admin'):
            flash('Please log in as administrator.', 'error')
            return redirect(url_for('admin_login'))
        admin = Admin.query.get(current_user.get_id())
        if not admin:
            session.clear()
            logout_user()
            flash('Administrator access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Database & Login Manager Initialization ---
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def unauthorized_handler():
    if request.path.startswith('/admin'):
        login_manager.login_view = 'admin_login'
    else:
        login_manager.login_view = 'customer_login'
    return redirect(url_for(login_manager.login_view))

login_manager.unauthorized_handler(unauthorized_handler)

@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
        # If we have an admin session, check admin first
        if session.get('is_admin'):
            admin = Admin.query.get(user_id)
            if admin:
                return admin
        else:
            # Otherwise check customer first
            customer = Customer.query.get(user_id)
            if customer:
                return customer
            # Fall back to admin check if no customer found
            admin = Admin.query.get(user_id)
            if admin:
                return admin
    except Exception as e:
        print(f"Error in user loader: {e}")
        return None

# --- Schema guard (adds missing columns pragmatically) ---
def ensure_schema():
    inspector = inspect(db.engine)
    columns = {col['name'] for col in inspector.get_columns('product')}
    if 'variant' not in columns:
        db.session.execute(text("ALTER TABLE product ADD COLUMN variant VARCHAR(50) NULL"))
        db.session.commit()
    if 'subcategory' not in columns:
        db.session.execute(text("ALTER TABLE product ADD COLUMN subcategory VARCHAR(50) NULL"))
        db.session.commit()

with app.app_context():
    try:
        ensure_schema()
    except Exception as e:
        # Avoid blocking startup; errors will appear in console
        pass

# --- Admin Routes ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    print("Admin login route accessed")
    
    # Clear any existing session and logout
    logout_user()
    session.clear()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt with username: {username}")
        
        # Explicitly query the Admin model
        admin = Admin.query.filter_by(username=username).first()
        print(f"Admin user found: {admin is not None}")

        if admin and admin.check_password(password):
            print("Password verification successful")
            
            # Set admin session flag before login
            session['is_admin'] = True
            session.permanent = True
            
            # Perform login
            login_user(admin, remember=True)
            
            # Force load the admin user
            admin = Admin.query.get(admin.id)
            
            print(f"Admin logged in, is_authenticated: {admin.is_authenticated}")
            print(f"Admin logged in, is_admin: {admin.is_admin}")
            print(f"Admin type: {type(admin)}")
            
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid administrator credentials.', 'danger')
            
    return render_template('admin/login.html')
            
    return render_template('admin/login.html')

    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.clear()
    logout_user()
    flash('You have been logged out of the admin panel.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    print("\nAdmin Dashboard Access Attempt:")
    print(f"Is authenticated: {current_user.is_authenticated}")
    
    # Check if we have admin session flag
    if not session.get('is_admin'):
        print("No admin session")
        session.clear()
        logout_user()
        return redirect(url_for('admin_login'))
    
    # Get the actual admin user from the database
    admin = Admin.query.get(current_user.get_id())
    if not admin:
        print("Admin not found in database")
        session.clear()
        logout_user()
        return redirect(url_for('admin_login'))
    
    print(f"Admin user found: {admin.username}")
    
    # Get real data from database
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    total_customers = Customer.query.count()
    pending_reservations_count = Reservation.query.filter_by(status='pending').count()
    
    # Get recent orders (last 10)
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    
    # Get pending reservations (last 5)
    pending_reservations_list = Reservation.query.filter_by(status='pending').order_by(
        Reservation.reservation_date.asc(),
        Reservation.reservation_time.asc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         admin=admin,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_customers=total_customers,
                         pending_reservations=pending_reservations_count,
                         pending_reservations_list=pending_reservations_list,
                         recent_orders=recent_orders)

@app.route('/admin/menu')
@login_required
@admin_required
def admin_menu():
    products = Product.query.order_by(Product.category, Product.name).all()
    categories = {}
    for p in products:
        categories.setdefault(p.category, []).append(p)
    return render_template('admin/menu.html', categories=categories)

@app.route('/admin/menu/management')
@login_required
@admin_required
def admin_menu_management():
    products = Product.query.order_by(Product.category, Product.name).all()
    categories = {}
    for p in products:
        categories.setdefault(p.category, []).append(p)
    return render_template('admin/menu_management.html', categories=categories)

@app.route('/admin/orders/management')
@login_required
@admin_required
def admin_order_management():
    # Optional filters
    status = request.args.get('status')
    search = request.args.get('q')

    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Order.customer_name.ilike(like)) |
            (Order.customer_phone.ilike(like)) |
            (Order.order_type.ilike(like))
        )

    orders_sql = query.order_by(Order.order_date.desc()).all()

    # Convert to JSON-serializable dicts and ensure id is string for slicing in template
    orders = []
    for o in orders_sql:
        orders.append({
            'id': str(o.id),
            'customer_name': o.customer_name,
            'customer_phone': o.customer_phone,
            'order_type': o.order_type,
            'order_date': o.order_date,
            'total_amount': o.total_amount,
            'status': o.status,
            'placed_outside_hours': getattr(o, 'placed_outside_hours', False),
            # Optional fields used by template JS (may be None)
            'customer_email': getattr(o, 'customer_email', None),
            'address': getattr(o, 'address', None),
            'special_instructions': getattr(o, 'special_instructions', None),
            'payment_method': getattr(o, 'payment_method', None),
        })

    return render_template('admin/order_management.html', orders=orders, status=status, q=search)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price', type=float)
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        available = request.form.get('available', 'on') == 'on'
        image_url = request.form.get('image_url')

        variant = request.form.get('variant')
        product = Product(name=name, description=description, price=price,
                          category=category, subcategory=subcategory, available=available, image_url=image_url, variant=variant)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin_menu_management'))

    return render_template('admin/add_product.html')

# Endpoints expected by templates in menu_management.html
@app.route('/admin/products/add', methods=['POST'])
@login_required
def admin_add_product():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price', type=float)
    category = request.form.get('category')
    subcategory = request.form.get('subcategory')
    image_url = None
    if 'image' in request.files and request.files['image']:
        image_file = request.files['image']
        if image_file.filename:
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(save_path)
            # Ensure the path starts with /static/uploads/
            image_url = '/static/uploads/' + filename

    variant = request.form.get('variant')
    product = Product(name=name, description=description, price=price, category=category, subcategory=subcategory, available=True, image_url=image_url, variant=variant)
    db.session.add(product)
    db.session.commit()
    flash('Product added successfully.', 'success')
    return redirect(url_for('admin_menu_management'))

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price', type=float)
        product.category = request.form.get('category')
        product.subcategory = request.form.get('subcategory')
        product.available = request.form.get('available') == 'on'
        product.image_url = request.form.get('image_url')
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin_menu_management'))

    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/products/update', methods=['POST'])
@login_required
def admin_update_product():
    product_id = request.form.get('product_id', type=int)
    product = Product.query.get_or_404(product_id)
    product.name = request.form.get('name')
    product.description = request.form.get('description')
    product.price = request.form.get('price', type=float)
    product.category = request.form.get('category')
    product.subcategory = request.form.get('subcategory')
    product.variant = request.form.get('variant')
    product.available = request.form.get('available') == 'on'
    if 'image' in request.files and request.files['image']:
        image_file = request.files['image']
        if image_file.filename:
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(save_path)
            # Ensure the path starts with /static/uploads/
            product.image_url = '/static/uploads/' + filename
    db.session.commit()
    flash('Product updated successfully.', 'success')
    return redirect(url_for('admin_menu_management'))

@app.route('/admin/products/delete', methods=['POST'])
@login_required
def admin_delete_product():
    product_id = request.form.get('product_id', type=int)
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin_menu_management'))

@app.route('/admin/products/toggle-availability', methods=['POST'])
@login_required
@admin_required
def toggle_product_availability():
    product_id = request.json.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required'}), 400
    
    product = Product.query.get_or_404(product_id)
    product.available = not product.available
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'available': product.available,
        'message': f'Product {"available" if product.available else "unavailable"} successfully'
    })


@app.route('/admin/orders/update-status', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status():
    try:
        order_id = request.form.get('order_id', type=int)
        status = request.form.get('status')
        
        if not order_id:
            flash('Invalid order ID.', 'error')
            return redirect(url_for('admin_order_management'))
        
        if not status:
            flash('Status is required.', 'error')
            return redirect(url_for('admin_order_management'))
        
        order = Order.query.get_or_404(order_id)
        order.status = status
        db.session.commit()
        flash('Order status updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order status: {str(e)}', 'error')
    
    return redirect(url_for('admin_order_management'))

@app.route('/admin/reservations/update-status', methods=['POST'])
@login_required
@admin_required
def admin_update_reservation_status():
    reservation_id = request.form.get('reservation_id', type=int)
    status = request.form.get('status')
    notes = request.form.get('admin_notes', '')
    
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = status
    reservation.admin_notes = notes
    db.session.commit()
    
    flash('Reservation status updated successfully.', 'success')
    return redirect(url_for('admin_reservations'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    # Get real orders from database
    orders_sql = Order.query.order_by(Order.order_date.desc()).all()
    
    # Convert to JSON-serializable dicts and ensure id is string for slicing in template
    orders = []
    for o in orders_sql:
        orders.append({
            'id': str(o.id),
            'customer_name': o.customer_name,
            'customer_phone': o.customer_phone,
            'order_type': o.order_type,
            'order_date': o.order_date,
            'total_amount': o.total_amount,
            'status': o.status,
            'placed_outside_hours': getattr(o, 'placed_outside_hours', False),
            # Optional fields used by template JS (may be None)
            'customer_email': getattr(o, 'customer_email', None),
            'address': getattr(o, 'address', None),
            'special_instructions': getattr(o, 'special_instructions', None),
            'payment_method': getattr(o, 'payment_method', None),
        })
    
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/api/new-orders-count')
@login_required
@admin_required
def admin_new_orders_count():
    """API endpoint to get count of pending/new orders"""
    try:
        # Get count of pending orders
        pending_count = Order.query.filter_by(status='pending').count()
        
        # Get count of orders placed in the last hour (new orders)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        new_orders_count = Order.query.filter(Order.order_date >= one_hour_ago).count()
        
        return jsonify({
            'pending_orders': pending_count,
            'new_orders': new_orders_count,
            'total_pending': pending_count
        })
    except Exception as e:
        print(f"Error getting order count: {e}")
        return jsonify({'pending_orders': 0, 'new_orders': 0, 'total_pending': 0}), 500

@app.route('/admin/reservations')
@login_required
@admin_required
def admin_reservations():
    # Get real reservations from database, ordered by date
    reservations = Reservation.query.order_by(
        Reservation.reservation_date.desc(),
        Reservation.reservation_time.desc()
    ).all()
    return render_template('admin/reservations.html', reservations=reservations)


# --- Command to create database and first admin user ---
# --- @app.route('/')
# --- def index():
    # --- if current_user.is_authenticated:
        # --- return redirect(url_for('admin_dashboard'))
    # --- return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_root():
    if current_user.is_authenticated:
        if hasattr(current_user, 'username') and current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
    return redirect(url_for('admin_login'))

# --- Customer Routes ---

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/menu')
def menu():
    """Display menu grouped by categories"""
    products = Product.query.filter_by(available=True).order_by(Product.category, Product.subcategory, Product.name).all()
    
    # Organize by subcategory (category name for display)
    categories = {}
    
    # Category name mappings for display
    category_mapping = {
        'Coffee Based': 'Coffee-based',
        'Coffee-based': 'Coffee-based',
        'Marinduque & Pinoy Dishes': 'Marinduque Pinoy Dishes',
        'Marinduque Pinoy Dishes': 'Marinduque Pinoy Dishes',
        'Beer & Liquour': 'Beer & Liquor',
        'Beer & Liquor': 'Beer & Liquor',
        'Soda & Juice in Can': 'Soda & Juice',
        'Soda & Juice': 'Soda & Juice'
    }
    
    # Populate categories by subcategory
    for product in products:
        subcategory = product.subcategory or 'Uncategorized'
        
        # Normalize category name using mapping
        display_category = category_mapping.get(subcategory, subcategory)
        
        if display_category not in categories:
            categories[display_category] = []
        categories[display_category].append(product)
    
    return render_template('menu.html', categories=categories)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Add item to cart"""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    if not product_id:
        flash('Invalid product', 'error')
        return redirect(url_for('menu'))
    
    product = Product.query.get_or_404(product_id)
    
    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = {}
    
    # Add or update item in cart
    if product_id in session['cart']:
        session['cart'][product_id] += quantity
    else:
        session['cart'][product_id] = quantity
    
    session.modified = True
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('menu'))

@app.route('/cart')
def cart():
    """Display shopping cart"""
    cart_items = []
    total = 0
    
    if 'cart' in session and session['cart']:
        for product_id, quantity in session['cart'].items():
            product = Product.query.get(product_id)
            if product:
                subtotal = product.price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                total += subtotal
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update-cart', methods=['POST'])
def update_cart():
    """Update cart item quantity"""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' in session and product_id in session['cart']:
        if quantity <= 0:
            del session['cart'][product_id]
        else:
            session['cart'][product_id] = quantity
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    """Remove item from cart"""
    product_id = request.form.get('product_id')
    
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True
        flash('Item removed from cart', 'success')
    
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    """Checkout page"""
    cart_items = []
    total = 0
    
    if 'cart' in session and session['cart']:
        for product_id, quantity in session['cart'].items():
            product = Product.query.get(product_id)
            if product:
                subtotal = product.price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                total += subtotal
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('menu'))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place-order', methods=['POST'])
def place_order():
    """Place order"""
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('menu'))
    
    # Check if we're within business hours
    current_time = datetime.now()
    outside_business_hours = not is_within_business_hours(current_time)
    
    # Get form data
    customer_name = request.form.get('customer_name')
    customer_email = request.form.get('customer_email')
    customer_phone = request.form.get('customer_phone')
    address = request.form.get('customer_address')
    order_type = request.form.get('order_type')
    payment_method = request.form.get('payment_method')
    special_instructions = request.form.get('special_instructions', '')
    
    # Validate required fields
    if not all([customer_name, customer_email, customer_phone, order_type, payment_method]):
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('checkout'))
    
    if order_type == 'delivery' and not address:
        flash('Delivery address is required for delivery orders', 'error')
        return redirect(url_for('checkout'))
    
    # Calculate total
    total = 0
    cart_items = []
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(product_id)
        if product:
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    # Add delivery fee if applicable
    delivery_fee = 3.99 if order_type == 'delivery' else 0
    total += delivery_fee
    
    # Create order
    order = Order(
        customer_id=current_user.id if current_user.is_authenticated and hasattr(current_user, 'email') else None,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        address=address if order_type == 'delivery' else None,
        order_type=order_type,
        payment_method=payment_method,
        total_amount=total,
        special_instructions=special_instructions
    )
    
    db.session.add(order)
    db.session.flush()  # Get order ID
    
    # Create order items
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product'].id,
            product_name=item['product'].name,
            quantity=item['quantity'],
            price=item['product'].price,
            subtotal=item['subtotal']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    # Clear cart
    session.pop('cart', None)
    
    # Show different success messages based on business hours
    if outside_business_hours:
        opening_hour, closing_hour = get_business_hours(current_time.date())
        if is_weekend(current_time.date()):
            hours_text = f'{opening_hour}:00 AM to {closing_hour-12}:00 PM'
        else:
            hours_text = f'{opening_hour}:00 AM to {closing_hour-12}:00 PM'
        
        flash(f'Order #{order.id} placed successfully! Note: The restaurant is currently closed. Our hours are {hours_text}. Your order will be processed when we open.', 'warning')
    else:
        flash(f'Order #{order.id} placed successfully!', 'success')
    
    return redirect(url_for('order_tracking', order_id=order.id))

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    """Reservations page"""
    if request.method == 'POST':
        guest_name = request.form.get('guest_name')
        guest_email = request.form.get('guest_email')
        guest_phone = request.form.get('guest_phone')
        reservation_date = datetime.strptime(request.form.get('reservation_date'), '%Y-%m-%d').date()
        reservation_time = datetime.strptime(request.form.get('reservation_time'), '%H:%M').time()
        party_size = int(request.form.get('number_of_people'))
        special_requests = request.form.get('special_requests', '')
        
        if party_size >= 13:
            flash('For parties of 13+ people, please call us directly at +1 (555) 123-4567', 'info')
            return redirect(url_for('reservations'))
        
        # Create a datetime object for the reservation
        reservation_datetime = datetime.combine(reservation_date, reservation_time)
        
        # Check if the reservation is within business hours
        if not is_within_business_hours(reservation_datetime):
            opening_hour, closing_hour = get_business_hours(reservation_date)
            if is_weekend(reservation_date):
                flash(f'Our weekend hours are {opening_hour}:00 AM to {closing_hour-12}:00 PM. Please select a time within these hours.', 'error')
            else:
                flash(f'Our weekday hours are {opening_hour}:00 AM to {closing_hour-12}:00 PM. Please select a time within these hours.', 'error')
            return redirect(url_for('reservations'))
        
        reservation = Reservation(
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            party_size=party_size,
            special_requests=special_requests
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        flash(f'Reservation confirmed! We will contact you soon to confirm.', 'success')
        return redirect(url_for('index'))
    
    return render_template('reservations.html')

@app.route('/order-lookup')
def order_lookup():
    """Order lookup page"""
    return render_template('order_lookup.html')

@app.route('/order-tracking', methods=['GET', 'POST'])
def order_tracking():
    """Order tracking page"""
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        try:
            order_id = int(order_id)
            order = Order.query.get_or_404(order_id)
            order_items = OrderItem.query.filter_by(order_id=order_id).all()
            return render_template('order_tracking.html', order=order, order_items=order_items)
        except ValueError:
            flash('Invalid order ID', 'error')
        except:
            flash('Order not found', 'error')
    
    # Check if order_id is provided as URL parameter
    order_id = request.args.get('order_id')
    if order_id:
        try:
            order_id = int(order_id)
            order = Order.query.get_or_404(order_id)
            order_items = OrderItem.query.filter_by(order_id=order_id).all()
            return render_template('order_tracking.html', order=order, order_items=order_items)
        except:
            flash('Order not found', 'error')
    
    return render_template('order_tracking.html')

# --- Customer Authentication Routes ---

@app.route('/register', methods=['GET', 'POST'])
def customer_register():
    """Customer registration"""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            full_name = request.form.get('full_name')
            phone = request.form.get('phone', '')
            address = request.form.get('address', '')
            city = request.form.get('city', '')
            postal_code = request.form.get('postal_code', '')
            
            if not all([email, password, full_name]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('customer_register'))
            
            if Customer.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('customer_register'))
            
            customer = Customer(
                email=email,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city,
                postal_code=postal_code
            )
            if not hasattr(customer, 'set_password'):
                flash('Internal error: password hashing not implemented', 'error')
                return redirect(url_for('customer_register'))
            customer.set_password(password)
            
            db.session.add(customer)
            db.session.commit()
            
            login_user(customer)
            # Ensure session is saved before redirect
            session.modified = True
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('customer_register'))
    
    return render_template('auth/customer_register.html')

@app.route('/login', methods=['GET', 'POST'])
def customer_login():
    """Customer login"""
    # First check if user is already logged in
    if current_user.is_authenticated:
        if hasattr(current_user, 'username'):  # Admin user
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))  # Customer user
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Only try to log in as customer, not admin
        customer = Customer.query.filter_by(email=email).first()
        if customer and customer.check_password(password):
            login_user(customer)
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/customer_login.html')

@app.route('/logout')
def customer_logout():
    """Customer logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def customer_profile():
    """Customer profile page"""
    if not hasattr(current_user, 'email'):
        # If it's an admin user, redirect to admin dashboard
        return redirect(url_for('admin_dashboard'))
    
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.order_date.desc()).all()
    reservations = Reservation.query.filter_by(
        guest_email=current_user.email
    ).order_by(Reservation.reservation_date.desc()).all()
    
    return render_template('customer/profile.html', orders=orders, reservations=reservations)

@app.route('/profile/orders')
@login_required
def order_history():
    """View order history"""
    if not hasattr(current_user, 'email'):
        return redirect(url_for('admin_dashboard'))
    
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('customer/order_history.html', orders=orders)

@app.cli.command("init-db")
def init_db_command():
    """Creates the database tables and a default admin user."""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        # Create admin user
        admin_user = Admin(username='admin')
        admin_user.set_password('password')  # Change this in a real application!
        db.session.add(admin_user)
        try:
            db.session.commit()
            print('Database initialized and default admin user created.')
        except Exception as e:
            db.session.rollback()
            print(f'Error creating admin user: {e}')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
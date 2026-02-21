"""
Real Estate CRM - Flask Application
A comprehensive CRM system for managing properties, clients, and deals
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_estate_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============== Database Models ==============

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='staff')  # admin, manager, staff
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    position = db.Column(db.String(50))  # e.g., Senior Agent, Junior Agent, etc.
    hire_date = db.Column(db.Date)
    commission_rate = db.Column(db.Float, default=3.0)
    is_active = db.Column(db.Boolean, default=True)
    avatar_color = db.Column(db.String(20), default='#1a365d')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    properties = db.relationship('Property', backref='agent', lazy=True, foreign_keys='Property.agent_id')
    clients = db.relationship('Client', backref='agent', lazy=True, foreign_keys='Client.agent_id')
    tasks = db.relationship('Task', backref='assigned_to', lazy=True, foreign_keys='Task.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role in ['admin', 'manager']


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    client_type = db.Column(db.String(20))  # buyer, seller, both
    status = db.Column(db.String(20), default='lead')  # lead, prospect, active, closed
    budget_min = db.Column(db.Float)
    budget_max = db.Column(db.Float)
    preferred_location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    source = db.Column(db.String(50))  # referral, website, social, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    interactions = db.relationship('Interaction', backref='client', lazy=True, cascade='all, delete-orphan')
    deals = db.relationship('Deal', backref='client', lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    property_type = db.Column(db.String(50))  # house, apartment, condo, land, commercial
    status = db.Column(db.String(20), default='available')  # available, pending, sold, rented
    listing_type = db.Column(db.String(20))  # sale, rent
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Float)
    sqft = db.Column(db.Integer)
    lot_size = db.Column(db.Float)
    year_built = db.Column(db.Integer)
    description = db.Column(db.Text)
    features = db.Column(db.Text)  # JSON string of features
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    deals = db.relationship('Deal', backref='property', lazy=True)
    showings = db.relationship('Showing', backref='property', lazy=True, cascade='all, delete-orphan')


class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    status = db.Column(db.String(30), default='initiated')  # initiated, negotiation, under_contract, closed, cancelled
    offer_price = db.Column(db.Float)
    final_price = db.Column(db.Float)
    commission_rate = db.Column(db.Float, default=3.0)
    closing_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def commission_amount(self):
        price = self.final_price or self.offer_price or 0
        return price * (self.commission_rate / 100) if price else 0


class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    interaction_type = db.Column(db.String(30))  # call, email, meeting, showing, note
    subject = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Showing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    client_email = db.Column(db.String(120))
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Activity(db.Model):
    """Track all staff activities for admin monitoring"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, updated, deleted, viewed, login, logout
    entity_type = db.Column(db.String(50))  # client, property, deal, task, showing, staff
    entity_id = db.Column(db.Integer)
    entity_name = db.Column(db.String(200))  # Store name for display even if entity is deleted
    details = db.Column(db.Text)  # Additional details in JSON format
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='activities', lazy=True)
    
    @property
    def action_icon(self):
        icons = {
            'created': 'fa-plus-circle',
            'updated': 'fa-edit',
            'deleted': 'fa-trash',
            'viewed': 'fa-eye',
            'login': 'fa-sign-in-alt',
            'logout': 'fa-sign-out-alt',
            'status_change': 'fa-exchange-alt',
            'scheduled': 'fa-calendar-plus'
        }
        return icons.get(self.action, 'fa-circle')
    
    @property
    def action_color(self):
        colors = {
            'created': 'success',
            'updated': 'info',
            'deleted': 'danger',
            'viewed': 'primary',
            'login': 'success',
            'logout': 'warning',
            'status_change': 'info',
            'scheduled': 'primary'
        }
        return colors.get(self.action, 'primary')


def log_activity(action, entity_type=None, entity_id=None, entity_name=None, details=None):
    """Helper function to log user activities"""
    if current_user.is_authenticated:
        activity = Activity(
            user_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(activity)
        db.session.commit()


# ============== Login Manager ==============

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============== Routes ==============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Log login activity
            activity = Activity(
                user_id=user.id,
                action='login',
                entity_type='session',
                entity_name=f'{user.full_name} logged in',
                ip_address=request.remote_addr
            )
            db.session.add(activity)
            db.session.commit()
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    log_activity('logout', 'session', entity_name=f'{current_user.full_name} logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_clients = Client.query.filter_by(agent_id=current_user.id).count()
    total_properties = Property.query.filter_by(agent_id=current_user.id).count()
    active_deals = Deal.query.join(Client).filter(
        Client.agent_id == current_user.id,
        Deal.status.in_(['initiated', 'negotiation', 'under_contract'])
    ).count()
    
    # Calculate total revenue from closed deals
    closed_deals = Deal.query.join(Client).filter(
        Client.agent_id == current_user.id,
        Deal.status == 'closed'
    ).all()
    total_revenue = sum(deal.commission_amount for deal in closed_deals)
    
    # Recent activities
    recent_clients = Client.query.filter_by(agent_id=current_user.id)\
        .order_by(Client.created_at.desc()).limit(5).all()
    recent_properties = Property.query.filter_by(agent_id=current_user.id)\
        .order_by(Property.created_at.desc()).limit(5).all()
    
    # Upcoming tasks
    upcoming_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status != 'completed'
    ).order_by(Task.due_date).limit(5).all()
    
    # Upcoming showings
    upcoming_showings = Showing.query.join(Property).filter(
        Property.agent_id == current_user.id,
        Showing.scheduled_date >= datetime.utcnow(),
        Showing.status == 'scheduled'
    ).order_by(Showing.scheduled_date).limit(5).all()
    
    return render_template('dashboard.html',
        total_clients=total_clients,
        total_properties=total_properties,
        active_deals=active_deals,
        total_revenue=total_revenue,
        recent_clients=recent_clients,
        recent_properties=recent_properties,
        upcoming_tasks=upcoming_tasks,
        upcoming_showings=upcoming_showings
    )


# ============== Client Routes ==============

@app.route('/clients')
@login_required
def clients():
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    search = request.args.get('search', '')
    
    query = Client.query.filter_by(agent_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(client_type=type_filter)
    if search:
        query = query.filter(
            db.or_(
                Client.first_name.ilike(f'%{search}%'),
                Client.last_name.ilike(f'%{search}%'),
                Client.email.ilike(f'%{search}%'),
                Client.phone.ilike(f'%{search}%')
            )
        )
    
    clients = query.order_by(Client.created_at.desc()).all()
    return render_template('clients.html', clients=clients)


@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        client = Client(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            client_type=request.form.get('client_type'),
            status=request.form.get('status', 'lead'),
            budget_min=float(request.form.get('budget_min') or 0),
            budget_max=float(request.form.get('budget_max') or 0),
            preferred_location=request.form.get('preferred_location'),
            source=request.form.get('source'),
            notes=request.form.get('notes'),
            agent_id=current_user.id
        )
        db.session.add(client)
        db.session.commit()
        log_activity('created', 'client', client.id, client.full_name, f'Added new client: {client.full_name}')
        flash('Client added successfully!', 'success')
        return redirect(url_for('clients'))
    
    return render_template('client_form.html', client=None)


@app.route('/clients/<int:id>')
@login_required
def view_client(id):
    client = Client.query.get_or_404(id)
    if client.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('clients'))
    
    interactions = Interaction.query.filter_by(client_id=id)\
        .order_by(Interaction.created_at.desc()).all()
    deals = Deal.query.filter_by(client_id=id).all()
    
    return render_template('client_detail.html', client=client, 
                         interactions=interactions, deals=deals)


@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    if client.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('clients'))
    
    if request.method == 'POST':
        client.first_name = request.form.get('first_name')
        client.last_name = request.form.get('last_name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.client_type = request.form.get('client_type')
        client.status = request.form.get('status')
        client.budget_min = float(request.form.get('budget_min') or 0)
        client.budget_max = float(request.form.get('budget_max') or 0)
        client.preferred_location = request.form.get('preferred_location')
        client.source = request.form.get('source')
        client.notes = request.form.get('notes')
        db.session.commit()
        log_activity('updated', 'client', client.id, client.full_name, f'Updated client: {client.full_name}')
        flash('Client updated successfully!', 'success')
        return redirect(url_for('view_client', id=id))
    
    return render_template('client_form.html', client=client)


@app.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    if client.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('clients'))
    
    client_name = client.full_name
    db.session.delete(client)
    db.session.commit()
    log_activity('deleted', 'client', id, client_name, f'Deleted client: {client_name}')
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('clients'))


@app.route('/clients/<int:id>/interaction', methods=['POST'])
@login_required
def add_interaction(id):
    client = Client.query.get_or_404(id)
    if client.agent_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    interaction = Interaction(
        client_id=id,
        interaction_type=request.form.get('interaction_type'),
        subject=request.form.get('subject'),
        notes=request.form.get('notes')
    )
    db.session.add(interaction)
    db.session.commit()
    flash('Interaction logged!', 'success')
    return redirect(url_for('view_client', id=id))


# ============== Property Routes ==============

@app.route('/properties')
@login_required
def properties():
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    listing_filter = request.args.get('listing', '')
    search = request.args.get('search', '')
    
    query = Property.query.filter_by(agent_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(property_type=type_filter)
    if listing_filter:
        query = query.filter_by(listing_type=listing_filter)
    if search:
        query = query.filter(
            db.or_(
                Property.title.ilike(f'%{search}%'),
                Property.address.ilike(f'%{search}%'),
                Property.city.ilike(f'%{search}%')
            )
        )
    
    properties = query.order_by(Property.created_at.desc()).all()
    return render_template('properties.html', properties=properties)


@app.route('/properties/add', methods=['GET', 'POST'])
@login_required
def add_property():
    if request.method == 'POST':
        prop = Property(
            title=request.form.get('title'),
            property_type=request.form.get('property_type'),
            status=request.form.get('status', 'available'),
            listing_type=request.form.get('listing_type'),
            price=float(request.form.get('price') or 0),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            zip_code=request.form.get('zip_code'),
            bedrooms=int(request.form.get('bedrooms') or 0),
            bathrooms=float(request.form.get('bathrooms') or 0),
            sqft=int(request.form.get('sqft') or 0),
            lot_size=float(request.form.get('lot_size') or 0),
            year_built=int(request.form.get('year_built') or 0),
            description=request.form.get('description'),
            features=request.form.get('features'),
            image_url=request.form.get('image_url'),
            agent_id=current_user.id
        )
        db.session.add(prop)
        db.session.commit()
        log_activity('created', 'property', prop.id, prop.title, f'Added property: {prop.title} - ${prop.price:,.0f}')
        flash('Property added successfully!', 'success')
        return redirect(url_for('properties'))
    
    return render_template('property_form.html', property=None)


@app.route('/properties/<int:id>')
@login_required
def view_property(id):
    prop = Property.query.get_or_404(id)
    if prop.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('properties'))
    
    showings = Showing.query.filter_by(property_id=id)\
        .order_by(Showing.scheduled_date.desc()).all()
    deals = Deal.query.filter_by(property_id=id).all()
    
    return render_template('property_detail.html', property=prop, 
                         showings=showings, deals=deals)


@app.route('/properties/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_property(id):
    prop = Property.query.get_or_404(id)
    if prop.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('properties'))
    
    if request.method == 'POST':
        prop.title = request.form.get('title')
        prop.property_type = request.form.get('property_type')
        prop.status = request.form.get('status')
        prop.listing_type = request.form.get('listing_type')
        prop.price = float(request.form.get('price') or 0)
        prop.address = request.form.get('address')
        prop.city = request.form.get('city')
        prop.state = request.form.get('state')
        prop.zip_code = request.form.get('zip_code')
        prop.bedrooms = int(request.form.get('bedrooms') or 0)
        prop.bathrooms = float(request.form.get('bathrooms') or 0)
        prop.sqft = int(request.form.get('sqft') or 0)
        prop.lot_size = float(request.form.get('lot_size') or 0)
        prop.year_built = int(request.form.get('year_built') or 0)
        prop.description = request.form.get('description')
        prop.features = request.form.get('features')
        prop.image_url = request.form.get('image_url')
        db.session.commit()
        log_activity('updated', 'property', prop.id, prop.title, f'Updated property: {prop.title}')
        flash('Property updated successfully!', 'success')
        return redirect(url_for('view_property', id=id))
    
    return render_template('property_form.html', property=prop)


@app.route('/properties/<int:id>/delete', methods=['POST'])
@login_required
def delete_property(id):
    prop = Property.query.get_or_404(id)
    if prop.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('properties'))
    
    prop_title = prop.title
    db.session.delete(prop)
    db.session.commit()
    log_activity('deleted', 'property', id, prop_title, f'Deleted property: {prop_title}')
    flash('Property deleted successfully!', 'success')
    return redirect(url_for('properties'))


@app.route('/properties/<int:id>/showing', methods=['POST'])
@login_required
def add_showing(id):
    prop = Property.query.get_or_404(id)
    if prop.agent_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    showing = Showing(
        property_id=id,
        client_name=request.form.get('client_name'),
        client_phone=request.form.get('client_phone'),
        client_email=request.form.get('client_email'),
        scheduled_date=datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%dT%H:%M'),
        status='scheduled'
    )
    db.session.add(showing)
    db.session.commit()
    log_activity('scheduled', 'showing', showing.id, prop.title, f'Scheduled showing for {prop.title} with {showing.client_name}')
    flash('Showing scheduled!', 'success')
    return redirect(url_for('view_property', id=id))


# ============== Deal Routes ==============

@app.route('/deals')
@login_required
def deals():
    status_filter = request.args.get('status', '')
    
    query = Deal.query.join(Client).filter(Client.agent_id == current_user.id)
    
    if status_filter:
        query = query.filter(Deal.status == status_filter)
    
    deals = query.order_by(Deal.created_at.desc()).all()
    return render_template('deals.html', deals=deals)


@app.route('/deals/add', methods=['GET', 'POST'])
@login_required
def add_deal():
    if request.method == 'POST':
        closing_date = request.form.get('closing_date')
        deal = Deal(
            client_id=int(request.form.get('client_id')),
            property_id=int(request.form.get('property_id')),
            status=request.form.get('status', 'initiated'),
            offer_price=float(request.form.get('offer_price') or 0),
            final_price=float(request.form.get('final_price') or 0) if request.form.get('final_price') else None,
            commission_rate=float(request.form.get('commission_rate') or 3.0),
            closing_date=datetime.strptime(closing_date, '%Y-%m-%d').date() if closing_date else None,
            notes=request.form.get('notes')
        )
        db.session.add(deal)
        db.session.commit()
        log_activity('created', 'deal', deal.id, deal.property.title, f'Created deal for {deal.property.title} with {deal.client.full_name}')
        flash('Deal created successfully!', 'success')
        return redirect(url_for('deals'))
    
    clients = Client.query.filter_by(agent_id=current_user.id).all()
    properties = Property.query.filter_by(agent_id=current_user.id).all()
    return render_template('deal_form.html', deal=None, clients=clients, properties=properties)


@app.route('/deals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_deal(id):
    deal = Deal.query.get_or_404(id)
    if deal.client.agent_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('deals'))
    
    if request.method == 'POST':
        old_status = deal.status
        closing_date = request.form.get('closing_date')
        deal.client_id = int(request.form.get('client_id'))
        deal.property_id = int(request.form.get('property_id'))
        deal.status = request.form.get('status')
        deal.offer_price = float(request.form.get('offer_price') or 0)
        deal.final_price = float(request.form.get('final_price') or 0) if request.form.get('final_price') else None
        deal.commission_rate = float(request.form.get('commission_rate') or 3.0)
        deal.closing_date = datetime.strptime(closing_date, '%Y-%m-%d').date() if closing_date else None
        deal.notes = request.form.get('notes')
        db.session.commit()
        
        if old_status != deal.status:
            log_activity('status_change', 'deal', deal.id, deal.property.title, f'Deal status changed: {old_status} → {deal.status}')
        else:
            log_activity('updated', 'deal', deal.id, deal.property.title, f'Updated deal for {deal.property.title}')
        flash('Deal updated successfully!', 'success')
        return redirect(url_for('deals'))
    
    clients = Client.query.filter_by(agent_id=current_user.id).all()
    properties = Property.query.filter_by(agent_id=current_user.id).all()
    return render_template('deal_form.html', deal=deal, clients=clients, properties=properties)


# ============== Task Routes ==============

@app.route('/tasks')
@login_required
def tasks():
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    
    tasks = query.order_by(Task.due_date).all()
    return render_template('tasks.html', tasks=tasks)


@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    due_date = request.form.get('due_date')
    task = Task(
        title=request.form.get('title'),
        description=request.form.get('description'),
        priority=request.form.get('priority', 'medium'),
        due_date=datetime.strptime(due_date, '%Y-%m-%dT%H:%M') if due_date else None,
        user_id=current_user.id
    )
    db.session.add(task)
    db.session.commit()
    log_activity('created', 'task', task.id, task.title, f'Created task: {task.title}')
    flash('Task added!', 'success')
    return redirect(url_for('tasks'))


@app.route('/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if task.status == 'completed':
        task.status = 'pending'
        task.completed_at = None
        log_activity('status_change', 'task', task.id, task.title, f'Reopened task: {task.title}')
    else:
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        log_activity('status_change', 'task', task.id, task.title, f'Completed task: {task.title}')
    
    db.session.commit()
    return redirect(url_for('tasks'))


@app.route('/tasks/<int:id>/delete', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    task_title = task.title
    db.session.delete(task)
    db.session.commit()
    log_activity('deleted', 'task', id, task_title, f'Deleted task: {task_title}')
    flash('Task deleted!', 'success')
    return redirect(url_for('tasks'))


# ============== Reports ==============

@app.route('/reports')
@login_required
def reports():
    # Sales by month
    current_year = datetime.utcnow().year
    monthly_data = []
    
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1)
        if month == 12:
            end_date = datetime(current_year + 1, 1, 1)
        else:
            end_date = datetime(current_year, month + 1, 1)
        
        deals = Deal.query.join(Client).filter(
            Client.agent_id == current_user.id,
            Deal.status == 'closed',
            Deal.closing_date >= start_date.date(),
            Deal.closing_date < end_date.date()
        ).all()
        
        total = sum(deal.final_price or deal.offer_price or 0 for deal in deals)
        commission = sum(deal.commission_amount for deal in deals)
        
        monthly_data.append({
            'month': start_date.strftime('%B'),
            'total_sales': total,
            'commission': commission,
            'deals': len(deals)
        })
    
    # Client sources - convert to list of lists for JSON serialization
    source_query = db.session.query(
        Client.source,
        db.func.count(Client.id)
    ).filter(
        Client.agent_id == current_user.id,
        Client.source.isnot(None)
    ).group_by(Client.source).all()
    source_data = [[row[0], row[1]] for row in source_query]
    
    # Property status - convert to list of lists for JSON serialization
    property_query = db.session.query(
        Property.status,
        db.func.count(Property.id)
    ).filter(
        Property.agent_id == current_user.id
    ).group_by(Property.status).all()
    property_status = [[row[0], row[1]] for row in property_query]
    
    return render_template('reports.html',
        monthly_data=monthly_data,
        source_data=source_data,
        property_status=property_status
    )


# ============== Staff Management Routes (Admin Only) ==============

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """Decorator to require manager or admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager():
            flash('Access denied. Manager privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/staff')
@login_required
@admin_required
def staff_list():
    """List all staff members"""
    status_filter = request.args.get('status', '')
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')
    
    query = User.query.filter(User.id != current_user.id)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    staff = query.order_by(User.created_at.desc()).all()
    
    # Get stats for each staff member
    staff_stats = {}
    for member in staff:
        clients_count = Client.query.filter_by(agent_id=member.id).count()
        properties_count = Property.query.filter_by(agent_id=member.id).count()
        closed_deals = Deal.query.join(Client).filter(
            Client.agent_id == member.id,
            Deal.status == 'closed'
        ).all()
        total_commission = sum(deal.commission_amount for deal in closed_deals)
        
        staff_stats[member.id] = {
            'clients': clients_count,
            'properties': properties_count,
            'deals': len(closed_deals),
            'commission': total_commission
        }
    
    return render_template('staff/staff_list.html', staff=staff, staff_stats=staff_stats)


@app.route('/staff/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_staff():
    """Add new staff member"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('staff/staff_form.html', staff=None)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('staff/staff_form.html', staff=None)
        
        hire_date = request.form.get('hire_date')
        
        # Generate random avatar color
        import random
        colors = ['#1a365d', '#2c5282', '#2b6cb0', '#38a169', '#d69e2e', '#805ad5', '#e53e3e', '#dd6b20']
        
        user = User(
            username=username,
            email=email,
            role=request.form.get('role', 'staff'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            position=request.form.get('position'),
            hire_date=datetime.strptime(hire_date, '%Y-%m-%d').date() if hire_date else None,
            commission_rate=float(request.form.get('commission_rate') or 3.0),
            is_active=True,
            avatar_color=random.choice(colors),
            created_by=current_user.id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'Staff member {user.full_name} created successfully!', 'success')
        return redirect(url_for('staff_list'))
    
    return render_template('staff/staff_form.html', staff=None)


@app.route('/staff/<int:id>')
@login_required
@admin_required
def view_staff(id):
    """View staff member details"""
    member = User.query.get_or_404(id)
    
    # Get staff statistics
    clients = Client.query.filter_by(agent_id=member.id).all()
    properties = Property.query.filter_by(agent_id=member.id).all()
    
    # Get deals
    deals = Deal.query.join(Client).filter(Client.agent_id == member.id).all()
    closed_deals = [d for d in deals if d.status == 'closed']
    active_deals = [d for d in deals if d.status in ['initiated', 'negotiation', 'under_contract']]
    
    total_commission = sum(deal.commission_amount for deal in closed_deals)
    total_sales = sum(deal.final_price or deal.offer_price or 0 for deal in closed_deals)
    
    # Recent activity
    recent_clients = Client.query.filter_by(agent_id=member.id)\
        .order_by(Client.created_at.desc()).limit(5).all()
    recent_properties = Property.query.filter_by(agent_id=member.id)\
        .order_by(Property.created_at.desc()).limit(5).all()
    
    stats = {
        'total_clients': len(clients),
        'total_properties': len(properties),
        'total_deals': len(deals),
        'closed_deals': len(closed_deals),
        'active_deals': len(active_deals),
        'total_commission': total_commission,
        'total_sales': total_sales
    }
    
    return render_template('staff/staff_detail.html', 
        member=member, 
        stats=stats,
        recent_clients=recent_clients,
        recent_properties=recent_properties,
        deals=deals
    )


@app.route('/staff/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(id):
    """Edit staff member"""
    member = User.query.get_or_404(id)
    
    if request.method == 'POST':
        # Check for duplicate username/email
        if request.form.get('username') != member.username:
            if User.query.filter_by(username=request.form.get('username')).first():
                flash('Username already exists', 'error')
                return render_template('staff/staff_form.html', staff=member)
        
        if request.form.get('email') != member.email:
            if User.query.filter_by(email=request.form.get('email')).first():
                flash('Email already registered', 'error')
                return render_template('staff/staff_form.html', staff=member)
        
        hire_date = request.form.get('hire_date')
        
        member.username = request.form.get('username')
        member.email = request.form.get('email')
        member.role = request.form.get('role', 'staff')
        member.first_name = request.form.get('first_name')
        member.last_name = request.form.get('last_name')
        member.phone = request.form.get('phone')
        member.position = request.form.get('position')
        member.hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date() if hire_date else None
        member.commission_rate = float(request.form.get('commission_rate') or 3.0)
        member.is_active = request.form.get('is_active') == 'on'
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            member.set_password(new_password)
        
        db.session.commit()
        flash('Staff member updated successfully!', 'success')
        return redirect(url_for('view_staff', id=id))
    
    return render_template('staff/staff_form.html', staff=member)


@app.route('/staff/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_staff_status(id):
    """Toggle staff active/inactive status"""
    member = User.query.get_or_404(id)
    member.is_active = not member.is_active
    db.session.commit()
    
    status = 'activated' if member.is_active else 'deactivated'
    flash(f'Staff member {member.full_name} has been {status}.', 'success')
    return redirect(url_for('staff_list'))


@app.route('/staff/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_staff(id):
    """Delete staff member"""
    member = User.query.get_or_404(id)
    
    if member.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('staff_list'))
    
    # Check if staff has any data
    has_clients = Client.query.filter_by(agent_id=member.id).first()
    has_properties = Property.query.filter_by(agent_id=member.id).first()
    
    if has_clients or has_properties:
        flash('Cannot delete staff member with assigned clients or properties. Deactivate instead.', 'error')
        return redirect(url_for('view_staff', id=id))
    
    db.session.delete(member)
    db.session.commit()
    flash('Staff member deleted successfully!', 'success')
    return redirect(url_for('staff_list'))


@app.route('/staff/<int:id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_staff_password(id):
    """Reset staff member password"""
    member = User.query.get_or_404(id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('edit_staff', id=id))
    
    member.set_password(new_password)
    db.session.commit()
    flash(f'Password for {member.full_name} has been reset.', 'success')
    return redirect(url_for('view_staff', id=id))


# ============== Staff Profile Route ==============

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Staff member can view/edit their own profile"""
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        
        # Change password if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            if current_user.check_password(current_password):
                if len(new_password) >= 6:
                    current_user.set_password(new_password)
                    flash('Password updated successfully!', 'success')
                else:
                    flash('New password must be at least 6 characters.', 'error')
            else:
                flash('Current password is incorrect.', 'error')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user statistics
    clients_count = Client.query.filter_by(agent_id=current_user.id).count()
    properties_count = Property.query.filter_by(agent_id=current_user.id).count()
    closed_deals = Deal.query.join(Client).filter(
        Client.agent_id == current_user.id,
        Deal.status == 'closed'
    ).all()
    total_commission = sum(deal.commission_amount for deal in closed_deals)
    
    stats = {
        'clients': clients_count,
        'properties': properties_count,
        'deals': len(closed_deals),
        'commission': total_commission
    }
    
    return render_template('staff/profile.html', stats=stats)


# ============== Activity Log Routes (Admin Only) ==============

@app.route('/activity-log')
@login_required
@admin_required
def activity_log():
    """View all staff activities"""
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity', '')
    date_filter = request.args.get('date', '')
    
    query = Activity.query
    
    if user_filter:
        query = query.filter_by(user_id=int(user_filter))
    if action_filter:
        query = query.filter_by(action=action_filter)
    if entity_filter:
        query = query.filter_by(entity_type=entity_filter)
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Activity.created_at) == filter_date)
    
    activities = query.order_by(Activity.created_at.desc()).limit(500).all()
    
    # Get all staff for filter dropdown
    staff = User.query.filter(User.id != current_user.id).all()
    
    # Get activity stats
    today = datetime.utcnow().date()
    today_count = Activity.query.filter(db.func.date(Activity.created_at) == today).count()
    
    week_start = today - timedelta(days=today.weekday())
    week_count = Activity.query.filter(Activity.created_at >= datetime.combine(week_start, datetime.min.time())).count()
    
    # Most active staff this week
    most_active = db.session.query(
        User.id, User.first_name, User.last_name, User.username,
        db.func.count(Activity.id).label('activity_count')
    ).join(Activity).filter(
        Activity.created_at >= datetime.combine(week_start, datetime.min.time())
    ).group_by(User.id).order_by(db.desc('activity_count')).limit(5).all()
    
    return render_template('activity_log.html', 
        activities=activities, 
        staff=staff,
        today_count=today_count,
        week_count=week_count,
        most_active=most_active
    )


@app.route('/activity-log/user/<int:user_id>')
@login_required
@admin_required
def user_activity_log(user_id):
    """View activities for a specific user"""
    user = User.query.get_or_404(user_id)
    activities = Activity.query.filter_by(user_id=user_id)\
        .order_by(Activity.created_at.desc()).limit(200).all()
    
    # Activity stats for this user
    today = datetime.utcnow().date()
    today_count = Activity.query.filter(
        Activity.user_id == user_id,
        db.func.date(Activity.created_at) == today
    ).count()
    
    week_start = today - timedelta(days=today.weekday())
    week_count = Activity.query.filter(
        Activity.user_id == user_id,
        Activity.created_at >= datetime.combine(week_start, datetime.min.time())
    ).count()
    
    total_count = Activity.query.filter_by(user_id=user_id).count()
    
    return render_template('user_activity_log.html', 
        user=user, 
        activities=activities,
        today_count=today_count,
        week_count=week_count,
        total_count=total_count
    )


# ============== Initialize Database ==============

def init_db():
    with app.app_context():
        db.create_all()
        # Create admin user if none exists
        if not User.query.filter_by(role='admin').first():
            admin_user = User(
                username='admin', 
                email='admin@estateflow.com', 
                role='admin',
                first_name='Admin',
                last_name='User',
                position='Administrator',
                is_active=True,
                avatar_color='#1a365d'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: username='admin', password='admin123'")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
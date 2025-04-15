from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456789'  
app.config['MYSQL_DB'] = 'fertilizer_management_system'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Secret key for session management
app.secret_key = '889302bc61c3b35d522d9048c7f15ae2'

# Initialize MySQL
mysql = MySQL(app)

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Login route for farmers
@app.route('/login/farmer', methods=['GET', 'POST'])
def farmer_login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Farmer WHERE email = %s AND password = %s', (email, password))
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['farmer_id'] = account['farmer_id']
            session['email'] = account['email']
            session['role'] = 'farmer'
            return redirect(url_for('farmer_dashboard'))
        else:
            msg = 'Incorrect email/password!'
    
    return render_template('login.html', role='farmer', msg=msg)

# Login route for officers
@app.route('/login/officer', methods=['GET', 'POST'])
def officer_login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM AgriculturalOfficer WHERE email = %s AND password = %s', (email, password))
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['officer_id'] = account['officer_id']
            session['email'] = account['email']
            session['role'] = 'officer'
            return redirect(url_for('officer_dashboard'))
        else:
            msg = 'Incorrect email/password!'
    
    return render_template('login.html', role='officer', msg=msg)

# Farmer registration
@app.route('/register/farmer', methods=['GET', 'POST'])
def farmer_register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'password' in request.form:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        land_area = request.form.get('land_area', 0)
        region = request.form.get('region', '')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Farmer WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not name or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO Farmer (name, email, password, phone, address, land_area, region) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                          (name, email, password, phone, address, land_area, region))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('farmer_login'))
    
    return render_template('register.html', role='farmer', msg=msg)

# Officer registration (only accessible by admin in real system)
@app.route('/register/officer', methods=['GET', 'POST'])
def officer_register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'password' in request.form:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        region = request.form.get('region', '')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM AgriculturalOfficer WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not name or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO AgriculturalOfficer (name, email, password, phone, region) VALUES (%s, %s, %s, %s, %s)',
                          (name, email, password, phone, region))
            mysql.connection.commit()
            msg = 'Officer has been successfully registered!'
            return redirect(url_for('officer_login'))
    
    return render_template('register.html', role='officer', msg=msg)

# Farmer dashboard
@app.route('/farmer/dashboard')
def farmer_dashboard():
    if 'loggedin' in session and session['role'] == 'farmer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get farmer details
        cursor.execute('SELECT * FROM Farmer WHERE farmer_id = %s', (session['farmer_id'],))
        farmer = cursor.fetchone()
        
        # Get cultivations
        cursor.execute('SELECT * FROM Cultivation WHERE farmer_id = %s ORDER BY planting_date DESC', (session['farmer_id'],))
        cultivations = cursor.fetchall()
        
        # Get fertilizer receipts
        cursor.execute('''
            SELECT r.receipt_id, r.quantity, r.issue_date, r.purpose, 
                   f.name as fertilizer_name, f.type as fertilizer_type,
                   s.name as store_name
            FROM Receives r
            JOIN Fertilizer f ON r.fertilizer_id = f.fertilizer_id
            JOIN Stores s ON r.store_id = s.store_id
            WHERE r.farmer_id = %s
            ORDER BY r.issue_date DESC
        ''', (session['farmer_id'],))
        receipts = cursor.fetchall()
        
        return render_template('farmer_dashboard.html', farmer=farmer, cultivations=cultivations, receipts=receipts)
    return redirect(url_for('farmer_login'))

# Officer dashboard
@app.route('/officer/dashboard')
def officer_dashboard():
    if 'loggedin' in session and session['role'] == 'officer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get officer details
        cursor.execute('SELECT * FROM AgriculturalOfficer WHERE officer_id = %s', (session['officer_id'],))
        officer = cursor.fetchone()
        
        # Get managed store
        cursor.execute('SELECT * FROM Stores WHERE manager_id = %s', (session['officer_id'],))
        store = cursor.fetchone()
        
        # Get farmers in region
        cursor.execute('SELECT * FROM Farmer WHERE region = %s', (officer['region'],))
        farmers = cursor.fetchall()
        
        # Get fertilizer stock
        cursor.execute('SELECT * FROM Fertilizer ORDER BY stock_quantity DESC')
        fertilizers = cursor.fetchall()
        
        # Get recent distributions
        cursor.execute('''
            SELECT r.receipt_id, r.quantity, r.issue_date, r.purpose, 
                   f.name as fertilizer_name, f.type as fertilizer_type,
                   s.name as store_name, fm.name as farmer_name
            FROM Receives r
            JOIN Fertilizer f ON r.fertilizer_id = f.fertilizer_id
            JOIN Stores s ON r.store_id = s.store_id
            JOIN Farmer fm ON r.farmer_id = fm.farmer_id
            WHERE r.officer_id = %s
            ORDER BY r.issue_date DESC
            LIMIT 10
        ''', (session['officer_id'],))
        distributions = cursor.fetchall()
        
        return render_template('officer_dashboard.html', officer=officer, store=store, 
                             farmers=farmers, fertilizers=fertilizers, distributions=distributions)
    return redirect(url_for('officer_login'))

# Add cultivation
@app.route('/farmer/cultivation/add', methods=['GET', 'POST'])
def add_cultivation():
    if 'loggedin' in session and session['role'] == 'farmer':
        if request.method == 'POST':
            crop_type = request.form['crop_type']
            planting_date = request.form['planting_date']
            harvest_date = request.form.get('harvest_date', None)
            area = request.form['area']
            status = request.form.get('status', 'Planted')
            
            cursor = mysql.connection.cursor()
            cursor.execute('''
                INSERT INTO Cultivation (farmer_id, crop_type, planting_date, harvest_date, area, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (session['farmer_id'], crop_type, planting_date, harvest_date, area, status))
            mysql.connection.commit()
            flash('Cultivation added successfully!', 'success')
            return redirect(url_for('farmer_dashboard'))
        
        return render_template('add_cultivation.html')
    return redirect(url_for('farmer_login'))

# Add fertilizer
@app.route('/officer/fertilizer/add', methods=['GET', 'POST'])
def add_fertilizer():
    if 'loggedin' in session and session['role'] == 'officer':
        if request.method == 'POST':
            name = request.form['name']
            type = request.form['type']
            composition = request.form['composition']
            suitable_crops = request.form['suitable_crops']
            price_per_kg = request.form['price_per_kg']
            stock_quantity = request.form.get('stock_quantity', 0)
            
            cursor = mysql.connection.cursor()
            cursor.execute('''
                INSERT INTO Fertilizer (name, type, composition, suitable_crops, price_per_kg, stock_quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (name, type, composition, suitable_crops, price_per_kg, stock_quantity))
            mysql.connection.commit()
            flash('Fertilizer added successfully!', 'success')
            return redirect(url_for('officer_dashboard'))
        
        return render_template('add_fertilizer.html')
    return redirect(url_for('officer_login'))

# Distribute fertilizer
@app.route('/officer/fertilizer/distribute', methods=['GET', 'POST'])
def distribute_fertilizer():
    if 'loggedin' in session and session['role'] == 'officer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            farmer_id = request.form['farmer_id']
            fertilizer_id = request.form['fertilizer_id']
            store_id = request.form['store_id']
            quantity = request.form['quantity']
            purpose = request.form['purpose']
            issue_date = datetime.now().strftime('%Y-%m-%d')
            
            # Check stock
            cursor.execute('SELECT stock_quantity FROM Fertilizer WHERE fertilizer_id = %s', (fertilizer_id,))
            fertilizer = cursor.fetchone()
            
            if fertilizer and float(fertilizer['stock_quantity']) >= float(quantity):
                # Update stock
                new_quantity = float(fertilizer['stock_quantity']) - float(quantity)
                cursor.execute('UPDATE Fertilizer SET stock_quantity = %s WHERE fertilizer_id = %s', 
                             (new_quantity, fertilizer_id))
                
                # Create distribution record
                cursor.execute('''
                    INSERT INTO Receives (farmer_id, fertilizer_id, store_id, officer_id, quantity, issue_date, purpose)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (farmer_id, fertilizer_id, store_id, session['officer_id'], quantity, issue_date, purpose))
                
                mysql.connection.commit()
                flash('Fertilizer distributed successfully!', 'success')
                return redirect(url_for('officer_dashboard'))
            else:
                flash('Insufficient stock!', 'danger')
        
        # Get farmers in officer's region
        cursor.execute('SELECT officer_id, region FROM AgriculturalOfficer WHERE officer_id = %s', (session['officer_id'],))
        officer = cursor.fetchone()
        
        cursor.execute('SELECT farmer_id, name FROM Farmer WHERE region = %s', (officer['region'],))
        farmers = cursor.fetchall()
        
        # Get fertilizers
        cursor.execute('SELECT fertilizer_id, name, stock_quantity FROM Fertilizer WHERE stock_quantity > 0')
        fertilizers = cursor.fetchall()
        
        # Get stores
        cursor.execute('SELECT store_id, name FROM Stores')
        stores = cursor.fetchall()
        
        return render_template('distribute_fertilizer.html', farmers=farmers, fertilizers=fertilizers, stores=stores)
    return redirect(url_for('officer_login'))

# Add Store
@app.route('/officer/store/add', methods=['GET', 'POST'])
def add_store():
    if 'loggedin' in session and session['role'] == 'officer':
        if request.method == 'POST':
            name = request.form['name']
            location = request.form['location']
            capacity = request.form['capacity']
            contact_phone = request.form['contact_phone']
            
            cursor = mysql.connection.cursor()
            cursor.execute('''
                INSERT INTO Stores (name, location, capacity, manager_id, contact_phone)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, location, capacity, session['officer_id'], contact_phone))
            mysql.connection.commit()
            flash('Store added successfully!', 'success')
            return redirect(url_for('officer_dashboard'))
        
        return render_template('add_store.html')
    return redirect(url_for('officer_login'))

# View All Stores
@app.route('/officer/stores')
def view_stores():
    if 'loggedin' in session and session['role'] == 'officer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all stores with manager names
        cursor.execute('''
            SELECT s.*, o.name as manager_name 
            FROM Stores s
            LEFT JOIN AgriculturalOfficer o ON s.manager_id = o.officer_id
        ''')
        stores = cursor.fetchall()
        
        # Get current officer's region
        cursor.execute('SELECT region FROM AgriculturalOfficer WHERE officer_id = %s', (session['officer_id'],))
        officer_region = cursor.fetchone()['region']
        
        return render_template('view_stores.html', stores=stores, officer_region=officer_region)
    return redirect(url_for('officer_login'))

# Edit Store
@app.route('/officer/store/edit/<int:store_id>', methods=['GET', 'POST'])
def edit_store(store_id):
    if 'loggedin' in session and session['role'] == 'officer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            name = request.form['name']
            location = request.form['location']
            capacity = request.form['capacity']
            contact_phone = request.form['contact_phone']
            
            cursor.execute('''
                UPDATE Stores 
                SET name = %s, location = %s, capacity = %s, contact_phone = %s
                WHERE store_id = %s
            ''', (name, location, capacity, contact_phone, store_id))
            mysql.connection.commit()
            flash('Store updated successfully!', 'success')
            return redirect(url_for('view_stores'))
        
        # Get store details
        cursor.execute('SELECT * FROM Stores WHERE store_id = %s', (store_id,))
        store = cursor.fetchone()
        
        # Get all officers for manager assignment
        cursor.execute('SELECT officer_id, name FROM AgriculturalOfficer')
        officers = cursor.fetchall()
        
        return render_template('edit_store.html', store=store, officers=officers)
    return redirect(url_for('officer_login'))

# Delete Store
@app.route('/officer/store/delete/<int:store_id>')
def delete_store(store_id):
    if 'loggedin' in session and session['role'] == 'officer':
        cursor = mysql.connection.cursor()
        try:
            cursor.execute('DELETE FROM Stores WHERE store_id = %s', (store_id,))
            mysql.connection.commit()
            flash('Store deleted successfully!', 'success')
        except:
            flash('Cannot delete store as it has related records!', 'danger')
        return redirect(url_for('view_stores'))
    return redirect(url_for('officer_login'))

# Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('farmer_id', None)
    session.pop('officer_id', None)
    session.pop('email', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
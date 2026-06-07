from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
import random
import joblib   # To load the ML model
import pandas as pd # To structure the ML inputs
import re       # Kept for compatibility, though no longer needed for city_code
import math

app = Flask(__name__)
app.secret_key = 'super_secret_organic_key' 
DB_NAME = 'database.db'

# --- LOAD ML MODEL ---
try:
    # UPDATED: Now loading the CatBoost model!
    delivery_model = joblib.load("models/catboost_delivery_time_model.pkl")
    print("✅ CatBoost ML Model Loaded Successfully!")
except Exception as e:
    delivery_model = None
    print(f"⚠️ Warning: Could not load ML model: {e}")

# --- 1. SETUP THE DATABASE ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Removed address from users, added contact_number
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, age INTEGER, contact_number TEXT)''')
        
        # NEW TABLE: User Addresses
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_addresses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, address_text TEXT, city_type TEXT, distance INTEGER)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS deliverers (id INTEGER PRIMARY KEY AUTOINCREMENT, deliverer_id TEXT UNIQUE, name TEXT, password TEXT, age INTEGER, vehicle_type TEXT, vehicle_condition INTEGER, vehicle_no TEXT, contact_number TEXT, rating REAL DEFAULT 5.0, rating_count INTEGER DEFAULT 1)''')
        
        # Added customer_contact, city_type, and distance to Orders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                customer_name TEXT,
                customer_contact TEXT,
                address TEXT,
                city_type TEXT,
                distance INTEGER,
                items TEXT,
                total_price REAL,
                status TEXT DEFAULT 'Pending',
                deliverer_id TEXT DEFAULT NULL,
                traffic TEXT DEFAULT NULL,
                weather TEXT DEFAULT NULL,
                multiple_deliveries INTEGER DEFAULT NULL,
                festival TEXT DEFAULT NULL
            )
        ''')
        conn.commit()

if not os.path.exists(DB_NAME):
    init_db()

# --- 2. LOGIN AND REGISTRATION ---
@app.route('/', methods=['GET', 'POST'])
def login():
    error, success = None, None
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'register_user':
            username, password, age = request.form.get('new_username'), request.form.get('new_password'), request.form.get('age')
            contact, address, city_type = request.form.get('contact_number'), request.form.get('address'), request.form.get('city_type')
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    # 1. Save the User
                    cursor.execute("INSERT INTO users (username, password, age, contact_number) VALUES (?, ?, ?, ?)", (username, password, age, contact))
                    user_id = cursor.lastrowid
                    
                    # 2. Save their first address with a random distance!
                    distance = random.randint(1, 25)
                    cursor.execute("INSERT INTO user_addresses (user_id, address_text, city_type, distance) VALUES (?, ?, ?, ?)", (user_id, address, city_type, distance))
                    conn.commit()
                success = "User account created! You can now log in."
            except sqlite3.IntegrityError:
                error = "Username already exists."
                
        elif action == 'register_deliverer':
            deliverer_id = request.form.get('deliverer_id')
            name = request.form.get('deliverer_name')
            password = request.form.get('deliverer_password')
            age = request.form.get('deliverer_age')
            vehicle_type = request.form.get('vehicle_type')
            vehicle_condition = request.form.get('vehicle_condition')
            contact = request.form.get('contact_number')
            vehicle_no = request.form.get('vehicle_no') # <-- Catches the new input
            
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    # Added vehicle_no to the INSERT statement
                    cursor.execute("INSERT INTO deliverers (deliverer_id, name, password, age, vehicle_type, vehicle_condition, vehicle_no, contact_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                   (deliverer_id, name, password, age, vehicle_type, vehicle_condition, vehicle_no, contact))
                    conn.commit()
                success = f"Account created! Your Login ID is: {deliverer_id}"
            except sqlite3.IntegrityError:
                error = "That ID already exists."
        else:
            username, password = request.form.get('username'), request.form.get('password')
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user[0]
                    return redirect(url_for('index'))
                    
                cursor.execute("SELECT * FROM deliverers WHERE name=? AND password=?", (username, password))
                deliverer = cursor.fetchone()
                if deliverer:
                    session['deliverer_id'] = deliverer[1] 
                    return redirect(url_for('deliver'))
            error = "Invalid username or password."
    return render_template('login.html', error=error, success=success)

# --- 3. STORE AND CHECKOUT ---
@app.route('/index')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Get User details
        cursor.execute("SELECT * FROM users WHERE id=?", (session['user_id'],))
        current_user = cursor.fetchone()
        
        # Get all User Addresses
        cursor.execute("SELECT * FROM user_addresses WHERE user_id=? ORDER BY id DESC", (session['user_id'],))
        user_addresses = cursor.fetchall()
        
    return render_template('index.html', user=current_user, addresses=user_addresses)

# --- NEW: Quick route to handle the offcanvas profile forms ---
@app.route('/manage_address', methods=['POST'])
def manage_address():
    if 'user_id' not in session: return redirect(url_for('login'))
    action = request.form.get('action')
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if action == 'add_address':
            new_address = request.form.get('address')
            distance = random.randint(1, 25) 
            
            # We hardcode "N/A" for city_type since the frontend doesn't use it anymore!
            cursor.execute("INSERT INTO user_addresses (user_id, address_text, city_type, distance) VALUES (?, ?, ?, ?)", 
                           (session['user_id'], new_address, "N/A", distance))
            conn.commit()
        elif action == 'delete_address':
            addr_id = request.form.get('address_id')
            cursor.execute("DELETE FROM user_addresses WHERE id=? AND user_id=?", (addr_id, session['user_id']))
            conn.commit()
            
    return redirect(url_for('index')) # Reload the store page instantly

# --- FETCH ADDRESSES FOR CHECKOUT ---
@app.route('/get_addresses', methods=['GET'])
def get_addresses():
    if 'user_id' not in session: 
        return jsonify({"error": "Not logged in"}), 401
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_addresses WHERE user_id=? ORDER BY id DESC", (session['user_id'],))
        addresses = [dict(row) for row in cursor.fetchall()]
    return jsonify(addresses)

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session: return jsonify({"error": "Please log in."}), 401
    data = request.get_json()
    items_str = ", ".join([f"{item['qty']}x {item['name']}" for item in data.get('cart')])
    address_id = data.get('address_id')
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Get user details
        cursor.execute("SELECT username, contact_number FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()
        
        # Get the selected address details
        cursor.execute("SELECT address_text, city_type, distance FROM user_addresses WHERE id=?", (address_id,))
        addr = cursor.fetchone()
        
        # Save the full order
        cursor.execute("""
            INSERT INTO orders (customer_id, customer_name, customer_contact, address, city_type, distance, items, total_price) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session['user_id'], user[0], user[1], addr[0], addr[1], addr[2], items_str, data.get('total')))
        conn.commit()
    return jsonify({"message": "Order placed successfully!"}), 200

# --- LIVE TRACKING & RATING ---
@app.route('/track_order', methods=['GET'])
def track_order():
    if 'user_id' not in session: return jsonify({"error": "Not logged in"})
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE customer_id=? AND status NOT IN ('Rejected', 'Delivered') ORDER BY id DESC LIMIT 1", (session['user_id'],))
        order = cursor.fetchone()
        
        if not order: return jsonify({"message": "No active orders found."})
        order_data = dict(order)
        
        if order['deliverer_id']:
            # Added 'age' and 'vehicle_condition' so the ML model can use them!
            # Added 'vehicle_no' to the SELECT query!
            cursor.execute("SELECT name, contact_number, vehicle_type, vehicle_no, rating, age, vehicle_condition FROM deliverers WHERE deliverer_id=?", (order['deliverer_id'],))
            deliverer = cursor.fetchone()
            
            if deliverer: 
                order_data['deliverer'] = dict(deliverer)
                
                # =========================================================
                # 🤖 ML PREDICTION LOGIC (CATBOOST)
                # =========================================================
                if order['status'] == 'Out for Delivery' and delivery_model:
                    try:
                        # 1. Format inputs EXACTLY as the model expects
                        
                        # WEATHER: HTML sends "Sandstorm", model wants "Sandstorms"
                        weather = str(order['weather'])
                        if weather == "Sandstorm":
                            weather = "Sandstorms"
                            
                        # TRAFFIC: DB has "LOW", model wants "Low "
                        traffic = str(order['traffic']).title() + " " 
                        
                        # VEHICLE CONDITION: Model wants "0", "1", or "2"
                        veh_cond = str(deliverer['vehicle_condition'])
                        
                        # MULTIPLE DELIVERIES: DB has 1, model wants "1.0"
                        mult_del = f"{float(order['multiple_deliveries'])}" 
                        
                        # FESTIVAL: DB has "Yes", model wants "Yes "
                        festival = str(order['festival']).title() + " "
                        
                        # Note: City and City_code parsing has been removed for CatBoost!
                        
                        # 2. Build the DataFrame with the 8 exact features
                        input_data = {
                            'Delivery_person_Age': [float(deliverer['age'])],
                            'Delivery_person_Ratings': [float(deliverer['rating'])],
                            'Weather_conditions': [weather],
                            'Road_traffic_density': [traffic],
                            'Vehicle_condition': [veh_cond],
                            'multiple_deliveries': [mult_del],
                            'Festival': [festival],
                            'distance': [float(order['distance'])]
                        }
                        df = pd.DataFrame(input_data)
                        
                        # 3. Predict!
                        predicted_minutes = delivery_model.predict(df)[0]
                        order_data['eta'] = math.ceil(predicted_minutes)
                        
                    except Exception as e:
                        print(f"Prediction Error: {e}")
                        order_data['eta'] = None # Fallback if error occurs

    return jsonify(order_data)

@app.route('/rate_deliverer', methods=['POST'])
def rate_deliverer():
    data = request.get_json()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rating, rating_count FROM deliverers WHERE deliverer_id=?", (data['deliverer_id'],))
        deliv = cursor.fetchone()
        if deliv:
            curr_rating, curr_count = deliv
            new_count = curr_count + 1
            new_rating = ((curr_rating * curr_count) + float(data['rating'])) / new_count
            cursor.execute("UPDATE deliverers SET rating=?, rating_count=? WHERE deliverer_id=?", (round(new_rating, 1), new_count, data['deliverer_id']))
            conn.commit()
    return jsonify({"message": "Thank you for your rating!"})

# --- 4. DELIVERY DASHBOARD ---
# --- 4. DELIVERY DASHBOARD ---
@app.route('/deliver')
def deliver():
    if 'deliverer_id' not in session: return redirect(url_for('login'))
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. Fetch all pending/active orders (Your existing code)
        cursor.execute("SELECT * FROM orders WHERE status NOT IN ('Rejected', 'Delivered') ORDER BY id DESC")
        all_orders = cursor.fetchall()
        
        # 2. NEW: Fetch the logged-in driver's complete profile data
        cursor.execute("SELECT * FROM deliverers WHERE deliverer_id=?", (session['deliverer_id'],))
        driver_profile = cursor.fetchone()
        
    # Pass BOTH the orders and the driver_profile to the HTML!
    return render_template('deliver.html', orders=all_orders, deliverer_id=session['deliverer_id'], driver=driver_profile)

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if data['status'] == 'Order Taken':
            cursor.execute("UPDATE orders SET status=?, deliverer_id=?, traffic=?, weather=?, multiple_deliveries=?, festival=? WHERE id=?", 
                           (data['status'], session['deliverer_id'], data.get('traffic'), data.get('weather'), data.get('multiple'), data.get('festival'), data['order_id']))
        else:
            cursor.execute("UPDATE orders SET status=?, deliverer_id=? WHERE id=?", (data['status'], session['deliverer_id'], data['order_id']))
        conn.commit()
    return jsonify({"message": "Status updated!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request, redirect, session, jsonify, send_from_directory
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG
from flask_cors import CORS
import os

app = Flask(__name__, static_folder="frontend")
app.secret_key = "quickdesk_secret"
CORS(app)

# DB connection
app.config['MYSQL_HOST'] = DB_CONFIG["HOST"]
app.config['MYSQL_USER'] = DB_CONFIG["USER"]
app.config['MYSQL_PASSWORD'] = DB_CONFIG["PASSWORD"]
app.config['MYSQL_DB'] = DB_CONFIG["DB"]

mysql = MySQL(app)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/register.html')
def serve_register():
    return send_from_directory(app.static_folder, 'register.html')

@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    email = data['email']
    password = generate_password_hash(data['password'])
    role = data['role']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)", (email, password, role))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Registration successful"})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data['email']
    password = data['password']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password, role FROM users WHERE email=%s", [email])
    user = cur.fetchone()
    cur.close()
    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        session['role'] = user[2]
        return jsonify({"message": "Login successful", "user_id": user[0], "role": user[2]})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT t.id, t.subject, t.status, c.name
        FROM tickets t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.created_at DESC
    """)
    tickets = cur.fetchall()
    cur.close()
    return jsonify([{
        "id": t[0],
        "subject": t[1],
        "status": t[2],
        "category": t[3]
    } for t in tickets])

@app.route('/api/categories', methods=['GET'])
def get_categories():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM categories")
    categories = cur.fetchall()
    cur.close()
    return jsonify([{"id": c[0], "name": c[1]} for c in categories])

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    subject = data['subject']
    description = data['description']
    category_id = data['category_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO tickets (subject, description, category_id, created_by)
        VALUES (%s, %s, %s, %s)
    """, (subject, description, category_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Ticket created successfully"})

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

if __name__ == '__main__':
    app.run(debug=True)
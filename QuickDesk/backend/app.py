from flask import Flask, request, session, jsonify, send_from_directory
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG
from flask_cors import CORS
import os

app = Flask(__name__)
app.secret_key = "quickdesk_secret"
CORS(app)

# Database config
app.config['MYSQL_HOST'] = DB_CONFIG["HOST"]
app.config['MYSQL_USER'] = DB_CONFIG["USER"]
app.config['MYSQL_PASSWORD'] = DB_CONFIG["PASSWORD"]
app.config['MYSQL_DB'] = DB_CONFIG["DB"]

mysql = MySQL(app)

# ---------- Serve HTML Pages and Other Files ----------
# Serve login.html from the frontend folder
@app.route('/')
def serve_login():
    return send_from_directory(os.path.join(app.root_path, 'frontend'), 'login.html')

# Serve register.html from the frontend folder
@app.route('/register')
def serve_register():
    return send_from_directory(os.path.join(app.root_path, 'frontend'), 'register.html')

# Serve other pages from frontend/pages folder
@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory(os.path.join(app.root_path, 'frontend', 'pages'), filename)

# Serve static files like CSS and JS from frontend directory
@app.route('/frontend/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(os.path.join(app.root_path, 'frontend'), filename)

# ---------- Auth ----------
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
        return jsonify({
            "message": "Login successful",
            "user_id": user[0],
            "email": email,
            "role": user[2]
        })
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"})

# ---------- Ticket APIs ----------
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

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    subject = data['subject']
    description = data['description']
    category_id = data['category_id']
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO tickets (subject, description, category_id, created_by)
        VALUES (%s, %s, %s, %s)
    """, (subject, description, category_id, user_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Ticket created successfully"})

# ---------- Category APIs ----------
@app.route('/api/categories', methods=['GET'])
def get_categories():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM categories")
    rows = cur.fetchall()
    cur.close()
    return jsonify([{"id": row[0], "name": row[1]} for row in rows])

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    name = data['name']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO categories (name) VALUES (%s)", [name])
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Category added"})

@app.route('/api/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM categories WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Category deleted"})

@app.route('/api/categories/stats', methods=['GET'])
def category_stats():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.id, c.name,
               SUM(t.status = 'Open') as open,
               SUM(t.status = 'In Progress') as in_progress,
               SUM(t.status = 'Resolved') as resolved
        FROM categories c
        LEFT JOIN tickets t ON t.category_id = c.id
        GROUP BY c.id
    """)
    rows = cur.fetchall()
    cur.close()
    return jsonify([{
        "id": r[0],
        "name": r[1],
        "open": int(r[2] or 0),
        "in_progress": int(r[3] or 0),
        "resolved": int(r[4] or 0)
    } for r in rows])

# ---------- Ping ----------
@app.route('/ping')
def ping():
    return "Backend is up!"

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)

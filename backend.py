from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import os
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)  # Permite requisições de outros dispositivos na rede

USERS_FILE = 'usuarios.json'
RECEITAS_FILE = 'receitas.json'
SESSIONS = {}  # token: email

# --- UTILITÁRIOS DE ARQUIVO ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_receitas():
    if not os.path.exists(RECEITAS_FILE):
        return {}
    try:
        with open(RECEITAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_receitas(receitas):
    with open(RECEITAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(receitas, f, ensure_ascii=False, indent=2)

# --- CRIA USUÁRIO ADMIN E RECEITAS SE NÃO EXISTIREM ---
def ensure_admin():
    users = load_users()
    admin = next((u for u in users if u['email'] == 'admin@admin.com'), None)
    if not admin:
        users.append({
            'email': 'admin@admin.com',
            'username': 'admin',
            'password_hash': generate_password_hash('admin')
        })
        save_users(users)
    receitas = load_receitas()
    if 'admin@admin.com' not in receitas:
        receitas['admin@admin.com'] = [
            {
                "id": 1,
                "name": "Pão Tradicional",
                "yield": 10,
                "ingredients": [
                    {"id": 1, "name": "Farinha de Trigo", "amount": 1000},
                    {"id": 2, "name": "Água Morna", "amount": 600},
                    {"id": 3, "name": "Fermento Biológico Seco", "amount": 10},
                    {"id": 4, "name": "Açúcar", "amount": 50},
                    {"id": 5, "name": "Sal", "amount": 20},
                    {"id": 6, "name": "Óleo", "amount": 50}
                ]
            }
        ]
        save_receitas(receitas)

ensure_admin()

# --- AUTENTICAÇÃO ---
def get_user_by_email(email):
    users = load_users()
    return next((u for u in users if u['email'] == email), None)

def get_user_by_username(username):
    users = load_users()
    return next((u for u in users if u['username'] == username), None)

def require_auth(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token not in SESSIONS:
            return jsonify({'error': 'Não autorizado'}), 401
        g.user_email = SESSIONS[token]
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# --- ENDPOINTS DE USUÁRIO ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    if not email or not username or not password:
        return jsonify({'error': 'Preencha todos os campos'}), 400
    if get_user_by_email(email):
        return jsonify({'error': 'Email já cadastrado'}), 400
    if get_user_by_username(username):
        return jsonify({'error': 'Nome de usuário já cadastrado'}), 400
    users = load_users()
    users.append({
        'email': email,
        'username': username,
        'password_hash': generate_password_hash(password)
    })
    save_users(users)
    # Cria espaço para receitas do novo usuário
    receitas = load_receitas()
    receitas[email] = []
    save_receitas(receitas)
    return jsonify({'status': 'ok'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not isinstance(password, str):
        return jsonify({'error': 'Senha inválida'}), 400
    user = get_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    token = str(uuid.uuid4())
    SESSIONS[token] = email
    return jsonify({'token': token, 'username': user['username'], 'email': user['email']})

@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token and token in SESSIONS:
        del SESSIONS[token]
    return jsonify({'status': 'ok'})

# --- ENDPOINTS DE RECEITAS (PROTEGIDOS) ---
@app.route('/receitas', methods=['GET'])
@require_auth
def get_receitas():
    receitas = load_receitas()
    return jsonify(receitas.get(g.user_email, []))

@app.route('/receitas', methods=['POST'])
@require_auth
def save_user_receitas():
    receitas = load_receitas()
    receitas[g.user_email] = request.json
    save_receitas(receitas)
    return jsonify({'status': 'ok'})

# --- SERVE FRONTEND ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
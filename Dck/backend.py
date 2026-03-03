from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)  # Permite requisições de outros dispositivos na rede

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    recipes = db.relationship('Recipe', backref='user', lazy=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_data = db.Column(db.Text, nullable=False) # JSON armazenado como texto

SESSIONS = {}  # token: email (Em memória, conforme original)

# Inicialização do Banco de Dados e Usuário Admin
with app.app_context():
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    db.create_all()
    
    admin = User.query.filter_by(email='admin@admin.com').first()
    if not admin:
        admin = User(
            email='admin@admin.com', 
            username='admin', 
            password_hash=generate_password_hash('admin')
        )
        db.session.add(admin)
        db.session.commit()
        
        default_recipe = [
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
        recipe_entry = Recipe(user_id=admin.id, recipe_data=json.dumps(default_recipe, ensure_ascii=False))
        db.session.add(recipe_entry)
        db.session.commit()

# --- AUTENTICAÇÃO ---
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
        
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já cadastrado'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Nome de usuário já cadastrado'}), 400
        
    new_user = User(
        email=email,
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()
    
    new_recipe = Recipe(user_id=new_user.id, recipe_data="[]")
    db.session.add(new_recipe)
    db.session.commit()
    
    return jsonify({'status': 'ok'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not isinstance(password, str):
        return jsonify({'error': 'Senha inválida'}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
        
    token = str(uuid.uuid4())
    SESSIONS[token] = email
    return jsonify({'token': token, 'username': user.username, 'email': user.email})

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
    user = User.query.filter_by(email=g.user_email).first()
    if not user:
        return jsonify([])
        
    recipe = Recipe.query.filter_by(user_id=user.id).first()
    if recipe and recipe.recipe_data:
        try:
            return jsonify(json.loads(recipe.recipe_data))
        except:
            return jsonify([])
    return jsonify([])

@app.route('/receitas', methods=['POST'])
@require_auth
def save_user_receitas():
    user = User.query.filter_by(email=g.user_email).first()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
        
    recipe = Recipe.query.filter_by(user_id=user.id).first()
    if not recipe:
        recipe = Recipe(user_id=user.id)
        db.session.add(recipe)
        
    recipe.recipe_data = json.dumps(request.json, ensure_ascii=False)
    db.session.commit()
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

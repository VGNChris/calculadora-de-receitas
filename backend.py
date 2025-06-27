from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)  # Permite requisições de outros dispositivos na rede

RECEITAS_FILE = 'receitas.json'

# Garante que o arquivo existe
if not os.path.exists(RECEITAS_FILE):
    with open(RECEITAS_FILE, 'w', encoding='utf-8') as f:
        json.dump([
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
        ], f, ensure_ascii=False, indent=2)

@app.route('/receitas', methods=['GET'])
def get_receitas():
    with open(RECEITAS_FILE, 'r', encoding='utf-8') as f:
        receitas = json.load(f)
    return jsonify(receitas)

@app.route('/receitas', methods=['POST'])
def save_receitas():
    receitas = request.json
    with open(RECEITAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(receitas, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "ok"})

# Opcional: servir o index.html e arquivos estáticos
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
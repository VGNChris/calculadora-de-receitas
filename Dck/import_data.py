import os
import json
import sys

# Garante que as importações locais vão funcionar para o script de importação
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from backend import app, db, User, Recipe

def import_data():
    root_dir = os.path.dirname(script_dir)
    users_file = os.path.join(root_dir, 'usuarios.json')
    receitas_file = os.path.join(root_dir, 'Calculadora_VP', 'receitas.json')
    
    with app.app_context():
        # Load users
        if os.path.exists(users_file):
            print(f"Lendo usuários de {users_file}...")
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                
            count_users = 0
            for u in users_data:
                email = u.get('email')
                if not email:
                    continue
                    
                if not User.query.filter_by(email=email).first():
                    new_user = User(
                        email=email,
                        username=u.get('username', email.split('@')[0]),
                        password_hash=u.get('password_hash', '')
                    )
                    db.session.add(new_user)
                    count_users += 1
            
            db.session.commit()
            print(f"Importados {count_users} novos usuários para o banco.")
        else:
            print(f"Arquivo não encontrado: {users_file}")
            
        # Load recipes
        if os.path.exists(receitas_file):
            print(f"Lendo receitas de {receitas_file}...")
            with open(receitas_file, 'r', encoding='utf-8') as f:
                try:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, list):
                        receitas_data = {'admin@admin.com': loaded_data}
                    else:
                        receitas_data = loaded_data
                except Exception as e:
                    print(f"Erro lendo JSON: {e}")
                    receitas_data = {}
                
            count_recipes = 0
            for email, recipes_list in receitas_data.items():
                user = User.query.filter_by(email=email).first()
                if user:
                    recipe = Recipe.query.filter_by(user_id=user.id).first()
                    if not recipe:
                        recipe = Recipe(user_id=user.id)
                        db.session.add(recipe)
                    recipe.recipe_data = json.dumps(recipes_list, ensure_ascii=False)
                    count_recipes += 1
            
            db.session.commit()
            print(f"Receitas importadas/atualizadas para {count_recipes} usuários.")
        else:
            print(f"Arquivo não encontrado: {receitas_file}")
            
    print("Migração concluída.")

if __name__ == '__main__':
    import_data()

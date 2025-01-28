from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from login import check_auth# Vérification des credentials
import secrets
import os
from user import get_all_users, delete_user, create_user, update_user
import mysql.connector


app = Flask(__name__)
app.secret_key = 'votre_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'  # Peut être Redis ou autre
CORS(app, supports_credentials=True)
COOKIE_MAX_AGE = 60 * 60 * 24  # 24 heures
SECURE_COOKIE = not os.getenv("FLASK_ENV") == "development"  # Désactiver secure=True en dev


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    user = check_auth(username, password)

    if user:

        response = make_response(jsonify({"message": "Login successful", "Session_id": secrets.token_hex(32), "isAdmin": 'admin' if user[4] else 'notAdmin' , "username" : user[1]}))
        
        # response.set_cookie(
        #     'session_token',
        #     session_token,
        #     httponly=True,
        #     ##secure=SECURE_COOKIE,
        #     max_age=COOKIE_MAX_AGE,
        #     path = '/'
        #     ##samesite='Lax'
        # )

        # user_role = 'admin' if user[4] else 'notAdmin'
        # response.set_cookie(
        #     'user_role',
        #     user_role,
        #     httponly=True,
        #     ##secure=False,  # Reste accessible pour le frontend
        #     max_age=COOKIE_MAX_AGE,
        #     path = '/'
        #     ##samesite='Lax'
        # )


        print(response)

        # (Optionnel) Stocker le token côté serveur pour validation future
        return response, 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/auth/check-session', methods=['GET'])
def check_session():
    session_token = request.cookies.get('session_token')
    user_role = request.cookies.get('user_role')

    if not session_token:
        return jsonify({"error": "No session cookie found"}), 401

    # (Optionnel) Valider le token dans une base de données ou cache

    return jsonify({"message": "Session active", "role": user_role}), 200


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"message": "Logged out"}))
    response.set_cookie('session_token', '', httponly=True, secure=SECURE_COOKIE, max_age=0)
    response.set_cookie('user_role', '', httponly=False, secure=False, max_age=0)
    return response, 200

@app.route('/api/auth/users', methods=['GET'])
def get_users():
    try:
        users = get_all_users()  # Récupère tous les utilisateurs depuis la DB via la fonction du fichier user.py
        return jsonify({"users": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/create-user', methods=['POST'])
def create_user_route():
    data = request.json
    if not data or 'username' not in data or 'password' not in data or 'email' not in data or 'is_admin' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    # Connexion à la base de données MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Admin",
        database="Pils_users_db"
    )
    cursor = conn.cursor()

    # Vérification si le username existe déjà
    query_check_username = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query_check_username, (data['username'],))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

    # Convertir 'is_admin' en entier (0 ou 1)
    is_admin = 1 if data['is_admin'] else 0

    try:
        created_user = create_user(data['username'], data['password'], data['email'], is_admin)
        if created_user:
            return jsonify({"message": "User created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create user"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/api/auth/update-user/<string:username>', methods=['PUT'])
def update_user_route(username):
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Récupérer l'utilisateur existant dans la base de données
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Admin",
            database="Pils_users_db"
        )
        cursor = conn.cursor(dictionary=True)

        # Obtenir les informations actuelles de l'utilisateur
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Mettre à jour uniquement les champs fournis
        updated_username = data.get('new_username', user['username'])
        updated_email = data.get('new_email', user['email'])
        updated_password = data.get('new_password', user['password'])
        updated_role = data.get('new_role', user['is_admin'])

        # Mise à jour dans la base de données
        update_query = """
            UPDATE users
            SET username = %s, email = %s, password = %s, is_admin = %s
            WHERE username = %s
        """
        cursor.execute(update_query, (updated_username, updated_email, updated_password, updated_role, username))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/delete-user/<string:username>', methods=['DELETE'])
def delete_user_route(username):
    try:
        deleted_user = delete_user(username)
        if deleted_user:
            return jsonify({"message": "User deleted successfully"}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000) 

import mysql.connector

# Configuration de la connexion à la base de données
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Admin",
    "database": "Pils_users_db"
}

def check_user_in_db(username, password):
    """
    Vérifie si un utilisateur existe dans la base de données.
    :param username: Nom d'utilisateur
    :param password: Mot de passe
    :return: True si l'utilisateur existe, sinon False
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))

        user = cursor.fetchone()  # Récupère une ligne correspondante si elle existe
        cursor.close()
        conn.close()

        return user is not None
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return False
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return False

# Liste des utilisateurs et mots de passe à vérifier
users_to_check = [
    {"username": "user1", "password": "pass1"},
    {"username": "admin", "password": "admin"},
    {"username": "user3", "password": "wrongpass"}
]

# Vérification pour chaque utilisateur
for user in users_to_check:
    username = user["username"]
    password = user["password"]
    if check_user_in_db(username, password):
        print(f"L'utilisateur {username} avec le mot de passe {password} existe dans la base de données.")
    else:
        print(f"L'utilisateur {username} avec le mot de passe {password} n'existe pas ou les informations sont incorrectes.")

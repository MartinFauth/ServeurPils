import mysql.connector


def check_auth(username, password):
    """
    Vérifie si un utilisateur existe dans la base de données.
    :param username: Nom d'utilisateur
    :param password: Mot de passe
    :return: True si l'utilisateur existe, sinon False
    """
    try:
        conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Admin",
        database="Pils_users_db"
    )
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))

        user = cursor.fetchone()  # Récupère une ligne correspondante si elle existe
        print(user)
        cursor.close()
        conn.close()

        return user
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return None
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return None

import mysql.connector


def create_user(username, email, password, is_admin):
    # Connexion à la base de données MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Admin",
        database="Pils_users_db"
    )
    cursor = conn.cursor()

    # Hashage du mot de passe
    ##hashed_password = bcrypt.hash(password)

    # Requête pour insérer un nouvel utilisateur
    query = "INSERT INTO users (username, email, password, is_admin) VALUES (%s, %s, %s, %s)"
    values = (username, email, password, is_admin)

    try:
        cursor.execute(query, values)
        conn.commit()  # Sauvegarde dans la base de données
        print(f"Utilisateur {username} créé avec succès!")
    except mysql.connector.Error as err:
        print(f"Erreur : {err}")
    finally:
        cursor.close()
        conn.close()

# Exemple d'appel à la fonction
create_user("caca", "caca", "caca", False)

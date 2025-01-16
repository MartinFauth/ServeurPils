import mysql.connector
##from passlib.hash import bcrypt

def get_all_users():
    # Connexion à la base de données MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Admin",
        database="Pils_users_db"
    )
    cursor = conn.cursor(dictionary=True)

    # Requête pour récupérer tous les utilisateurs
    query = "SELECT * FROM users"

    try:
        cursor.execute(query)
        users = cursor.fetchall()  # Récupérer tous les utilisateurs
        if users:
            for user in users:
                print(user)
        else:
            print("Aucun utilisateur trouvé.")
    except mysql.connector.Error as err:
        print(f"Erreur : {err}")
    finally:
        cursor.close()
        conn.close()

# Exemple d'appel à la fonction
get_all_users()

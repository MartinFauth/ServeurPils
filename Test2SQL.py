import mysql.connector


def delete_user(user_id):
    # Connexion à la base de données MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Admin",
        database="Pils_users_db"
    )
    cursor = conn.cursor()

    # Requête pour supprimer un utilisateur
    query = "DELETE FROM users WHERE id = %s"
    values = (user_id,)

    try:
        cursor.execute(query, values)
        conn.commit()  # Sauvegarde de la suppression
        if cursor.rowcount > 0:
            print(f"Utilisateur avec ID {user_id} supprimé avec succès!")
        else:
            print(f"Aucun utilisateur trouvé avec l'ID {user_id}.")
    except mysql.connector.Error as err:
        print(f"Erreur : {err}")
    finally:
        cursor.close()
        conn.close()

# Exemple d'appel à la fonction
delete_user(3)  # Suppression de l'utilisateur avec ID 1

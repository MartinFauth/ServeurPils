import MySQLdb

# Configuration de la connexion à la base de données
db_config = {
    "host": "localhost",  # Remplacez par l'hôte de votre base de données
    "user": "root",       # Remplacez par votre utilisateur MySQL
    "passwd": "Admin",    # Remplacez par votre mot de passe MySQL
    "db": "alerts_list"   # Remplacez par le nom de votre base de données
}

def delete_all_alertes():
    try:
        # Connexion à la base de données
        db = MySQLdb.connect(**db_config)
        cursor = db.cursor()

        # Requête SQL pour supprimer toutes les alertes
        query = "DELETE FROM alerts_list"
        cursor.execute(query)
        db.commit()

        print("Toutes les alertes ont été supprimées avec succès.")

    except MySQLdb.Error as e:
        print(f"Erreur lors de la suppression des alertes : {e}")

    finally:
        # Fermeture de la connexion
        if db:
            db.close()

if __name__ == "__main__":
    delete_all_alertes()

from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
import json
import asyncio
from datetime import datetime
import threading
import base64
import mysql.connector

def get_all_users(): 
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Admin",
            database="Pils_users_db"
        )
        cursor = conn.cursor()

        # Exécution de la requête pour récupérer tous les utilisateurs
        query = "SELECT * FROM users"
        cursor.execute(query)

        # Récupérer toutes les lignes de la requête
        users = cursor.fetchall()

        # Création d'une liste de dictionnaires pour chaque utilisateur
        user_list = []
        for user in users:
            user_dict = {
                "id": user[0],       # Assurez-vous que les indices correspondent à vos colonnes
                "username": user[1], # Exemple : index 1 pour 'username'
                "adresse": user[2], # Exemple : index 2 pour 'password'
                "droits": "admin" if user[4] else "not admin"   # Exemple : index 3 pour 'role'
            }
            user_list.append(user_dict)

        # Fermeture des ressources
        cursor.close()
        conn.close()

        # Retourner la liste des utilisateurs
        print(user_list)
        return user_list

    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return None
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return None


def update_user(username, new_username, new_email, new_password, new_role):
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Admin",
            database="Pils_users_db"
        )
        cursor = conn.cursor()

        # Requête SQL pour mettre à jour l'utilisateur
        query = """
            UPDATE users
            SET username = %s, password = %s, email = %s, is_admin = %s WHERE username = %s
        """
        
        # Exécution de la requête avec les nouvelles valeurs n
        cursor.execute(query, (new_username, new_password, new_email, new_role, username ))

        # Commit de la transaction pour appliquer les changements
        conn.commit()

        # Vérification si la mise à jour a affecté des lignes
        if cursor.rowcount > 0:
            print(f"Utilisateur {username} mis à jour avec succès.")
        else:
            print(f"Aucun utilisateur trouvé avec l'ID {username}.")

        # Fermeture des ressources
        cursor.close()
        conn.close()

        return True

    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return False
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return False


def delete_user(username):
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Admin",
            database="Pils_users_db"
        )
        cursor = conn.cursor()

        # Requête SQL pour supprimer un utilisateur
        query = "DELETE FROM users WHERE username = %s"
        
        # Exécution de la requête pour supprimer l'utilisateur
        cursor.execute(query, (username,))

        # Commit de la transaction pour appliquer les changements
        conn.commit()

        # Vérification si la suppression a affecté des lignes
        if cursor.rowcount > 0:
            print(f"Utilisateur {username} supprimé avec succès.")
        else:
            print(f"Aucun utilisateur trouvé avec l'ID {username}.")

        # Fermeture des ressources
        cursor.close()
        conn.close()

        return True

    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return False
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return False


def create_user(username, password, mail, admin):
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Admin",
            database="Pils_users_db"
        )
        cursor = conn.cursor()

        # Requête SQL pour insérer un nouvel utilisateur
        query = "INSERT INTO users (username, password, email, is_admin) VALUES (%s, %s, %s,%s)"
        
        # Exécution de la requête pour insérer un nouvel utilisateur
        cursor.execute(query, (username, password, mail, admin))

        # Commit de la transaction pour appliquer les changements
        conn.commit()

        # Vérification si l'insertion a réussi
        if cursor.rowcount > 0:
            print(f"Nouvel utilisateur {username} créé avec succès.")
        else:
            print("Erreur lors de la création de l'utilisateur.")

        # Fermeture des ressources
        cursor.close()
        conn.close()

        return True

    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return False
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return False


##get_all_users()
##create_user('username1','password1','email1','12')
##update_user('caca', 'pipi', 'fdp', 'new_password', '0')
##delete_user('pipi')
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
import json
import asyncio
from datetime import datetime
import threading
import base64
import mysql.connector

# Fonction pour vérifier l'authentification dans la base de données
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
        print("user =================== {user}")
        cursor.close()
        conn.close()

        return user is not None
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return False
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Nouveau client tente de se connecter...")

    try:
        # Recevoir le premier message pour l'authentification
        print("En attente d'un message du client.")
        await websocket.accept()
        data = await websocket.receive_text()
        print(f"Message d'authentification reçu : {data}")

        # On suppose que le message est un JSON valide
        request = json.loads(data)

        if request["type"] == "auth":
            username = request["data"]["username"]
            password = request["data"]["password"]
            print(f"Authentification demandée pour : {username}")

            if check_auth(username, password):
                # Accepter la connexion uniquement si l'utilisateur est valide
                print(f"Utilisateur {username} authentifié avec succès.")
                response = {"status": "success", "message": "Connexion acceptée"}
                await websocket.send_text(json.dumps(response))

                # Gestion des messages après l'authentification
                while True:
                    data = await websocket.receive_text()
                    print(f"Message reçu du client : {data}")
                    await websocket.send_text(f"Message reçu : {data}")
            else:
                response = {"status": "error", "message": "Nom d'utilisateur ou mot de passe incorrect"}
                print(f"Échec d'authentification pour l'utilisateur : {username}")
                await websocket.send_text(json.dumps(response))
                ##await websocket.close()  # Fermer la connexion si l'authentification échoue
                
        else:
            print(f"Type de message inconnu reçu : {request['type']}")
            await websocket.close()  # Fermer la connexion pour un type de message invalide

    except WebSocketDisconnect:
        print("Client déconnecté.")
    except Exception as e:
        print(f"Erreur inattendue dans la gestion de la WebSocket : {e}")


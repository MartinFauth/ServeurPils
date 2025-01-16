from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
import json
import asyncio
from datetime import datetime
import threading
import base64
import mysql.connector

app = FastAPI()

# Stockage temporaire des connexions actives
connected_clients = []

# Variable pour générer un ID unique
alert_id_counter = 1

# Fonction de logging
def log_message(message):
    """Log un message reçu sur la WebSocket."""
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
    print(log_entry)  # Affiche dans la console
    try:
        with open("websocket_logs.txt", "a") as log_file:
            log_file.write(log_entry)
        print("Message loggé avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans le fichier de log : {e}")

def encode_video_to_base64(video_path):
    ##print(f"Encodage de la vidéo : {video_path}")
    try:
        with open(video_path, "rb") as video_file:
            encoded_video = base64.b64encode(video_file.read()).decode("utf-8")
        #print("Vidéo encodée avec succès.")
        return encoded_video
    except Exception as e:
        print(f"Erreur lors de l'encodage de la vidéo : {e}")
        return ""

# Fonction pour vérifier l'authentification dans la base de données

def check_auth(username, password):
    ##print("cacacacacacac")
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Admin",
            database="Pils_users_db"
        )
        cursor = conn.cursor(dictionary=True)
        print("Curseur créé avec succès.")

        query = """
            SELECT * FROM users
            WHERE username = %s AND password = %s
            """
        print("Exécution de la requête SQL.")
        cursor.execute(query, (username, password))

        user = cursor.fetchone()
        print(f"Résultat de la requête : {user}")

        cursor.close()
        conn.close()
        print("Connexion à la base de données fermée.")

        return user is not None
    
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
        return False
    except Exception as e:
        print(f"Erreur inattendue lors de la vérification de l'utilisateur : {e}")
        return False
    

# Fonction pour envoyer une alerte toutes les 10 secondes avec un ID et une heure dynamique
async def send_alert_periodically():
    global alert_id_counter
    #print("Fonction d'envoi d'alertes démarrée.")
    while True:
      #  print("Préparation de l'alerte à envoyer.")
        alert_id = alert_id_counter
        alert_id_counter += 1

        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")

        alert = {
            "id": alert_id,
            "camera": f"Caméra {alert_id}",
            "date": current_date,
            "heure": current_time,
            "statut": "En cours",
            "video": encode_video_to_base64("video1.mp4"),
        }

        if connected_clients:
       #     print(f"Envoi de l'alerte {alert_id} aux clients connectés.")
            for client in connected_clients:
                await client.send_text(json.dumps({"type": "alert", "data": alert}))
        #    print(f"Alerte {alert_id} envoyée avec succès.")
        else:
            print("Aucun client connecté pour recevoir l'alerte.")

        await asyncio.sleep(10)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Nouveau client tente de se connecter.")
    await websocket.accept()
    connected_clients.append(websocket)
    print("Client connecté avec succès. Total des clients connectés :", len(connected_clients))

    try:
        while True:
            print("En attente d'un message du client.")
            data = await websocket.receive_text()
            print(f"Message reçu : {data}")
            log_message(data)

            request = json.loads(data)
            if request["type"] == "auth":
                username = request["username"]
                password = request["password"]
                print(f"Authentification demandée pour : {username}")

                if check_auth(username, password):
                    response = {"status": "success", "message": "Authentifié"}
                    print(f"Utilisateur {username} authentifié avec succès.")
                    await websocket.send_text(json.dumps(response))
                    log_message(f"Réponse envoyée : {response}")
                else:
                    response = {"status": "error", "message": "Nom d'utilisateur ou mot de passe incorrect"}
                    print(f"Échec d'authentification pour l'utilisateur : {username}")
                    await websocket.send_text(json.dumps(response))
                    log_message(f"Réponse envoyée : {response}")

            elif request["type"] == "send_alert":
                alert = request["alert"]
                print(f"Envoi manuel d'une alerte : {alert}")
                for client in connected_clients:
                    await client.send_text(json.dumps({"type": "alert", "data": alert}))

            elif request["type"] == "update_status":
                alert_id = request["data"]["id"]
                statut = request["data"]["statut"]
                print(f"Statut de l'alerte {alert_id} mis à jour : {statut}")
                log_message(f"Alerte {alert_id} mise à jour avec le statut : {statut}")

    except WebSocketDisconnect:
        print("Client déconnecté.")
        connected_clients.remove(websocket)
        print("Total des clients connectés après déconnexion :", len(connected_clients))
    except Exception as e:
        print(f"Erreur inattendue dans la gestion de la WebSocket : {e}")

# Lance la fonction d'envoi d'alertes toutes les 10 secondes dans un thread
def start_alert_sending():
    print("Lancement du thread d'envoi d'alertes.")
    asyncio.run(send_alert_periodically())

@app.on_event("startup")
async def startup_event():
    print("Lancement de l'envoi d'alertes périodiques.")
    thread = threading.Thread(target=start_alert_sending)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    print("Démarrage de l'application FastAPI.")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

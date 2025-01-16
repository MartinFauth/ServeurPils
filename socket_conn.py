import asyncio
import websockets
import json
from datetime import datetime

# Définir l'URL de ton serveur WebSocket
SERVER_URI = "ws://localhost:8765"  # Change l'URL si nécessaire

async def connect_to_websocket(uri):
    # Établir une connexion WebSocket au serveur
    print("attente de connexion")
    async with websockets.connect(uri) as websocket:
        print(f"Connecté au WebSocket sur {uri}")

        # Boucle infinie pour envoyer et recevoir des messages
        while True:
            # Attendre un message du serveur
            message = await websocket.recv()
            print(f"Message reçu : {message}")

            # Exemple de traitement d'un message (à ajuster selon ton application)
            try:
                data = json.loads(message)
                if data["type"] == "alerte":
                    # Traiter l'alerte (par exemple, mettre à jour la base de données)
                    alert_data = data["alert"]
                    print(f"Nouvelle alerte reçue : {alert_data}")
                    # Ici tu pourrais appeler une fonction pour mettre à jour ta base de données
                else:
                    print("Type de message inconnu")
            except json.JSONDecodeError:
                print("Erreur lors du décodage du message JSON")

 

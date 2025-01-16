import cv2
import os
import json
import time
import numpy as np
from ultralytics import YOLO
from sort import Sort
import torch
import websockets
import asyncio
import threading

class ChildTrackingSystem:
    def __init__(self, model_path, watch_dir, output_dir, websocket_port=8765):
        # Initialisation du device (CPU ou GPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Appareil utilisé : {self.device}")

        # Chargement du modèle
        self.model = YOLO(model_path)

        # Dossiers
        self.watch_dir = watch_dir
        self.output_dir = output_dir

        # Gestion des alertes
        self.alerted_ids = set()

        # Tracker (Sort)
        self.tracker = Sort(max_age=30, min_hits=3, iou_threshold=0.2)

        # Paramètre de la connexion WebSocket
        self.websocket_port = websocket_port
        self.websocket_clients = set()  # Liste des clients connectés

        # Démarrer le serveur WebSocket dans un thread séparé
        self.websocket_thread = threading.Thread(target=self.start_websocket_server)
        self.websocket_thread.start()

    async def websocket_handler(self, websocket, path):
        """Gérer les connexions WebSocket entrantes"""
        self.websocket_clients.add(websocket)
        try:
            while True:
                await websocket.recv()
        except websockets.ConnectionClosed:
            print("Client WebSocket déconnecté")
        finally:
            self.websocket_clients.remove(websocket)

    def start_websocket_server(self):
        """Lancer un serveur WebSocket qui écoute les connexions"""
        start_server = websockets.serve(self.websocket_handler, "127.0.0.1", self.websocket_port)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_server)
        loop.run_forever()

    def send_to_websocket(self, message):
        """Envoyer un message à tous les clients connectés via WebSocket"""
        if self.websocket_clients:
            for client in self.websocket_clients:
                try:
                    asyncio.run(client.send(json.dumps(message)))
                    print(f"Message envoyé : {message}")
                except Exception as e:
                    print(f"Erreur d'envoi du message : {e}")
        else:
            print("Aucun client WebSocket connecté")

    def save_alert(self, alert_id, alert_data, frames, fps, frame_size):
        """
        Sauvegarde une alerte sous forme de fichier JSON et extrait une vidéo correspondante.
        Si l'alerte dure moins de 5 secondes, la vidéo sera prolongée à 7-8 secondes en ajoutant des frames.
        """
        # Création du dossier pour les alertes si nécessaire
        alert_dir = os.path.join(self.output_dir, "alerts")
        if not os.path.exists(alert_dir):
            os.makedirs(alert_dir)

        # Sauvegarde du fichier JSON
        json_path = os.path.join(alert_dir, f"alert_{alert_id}.json")
        alert_data['websocket'] = False  # Par défaut, on définit websocket à False

        # Vérifier si un client WebSocket est connecté
        if self.websocket_clients:
            alert_data['websocket'] = True  # Si WebSocket est connecté, modifier à True

        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(alert_data, json_file, indent=4, ensure_ascii=False)

        # Calcul de la durée de la vidéo de l'alerte
        alert_duration_in_sec = len(frames) / fps  # Durée en secondes
        alert_duration_in_ms = alert_duration_in_sec * 1000  # Conversion en millisecondes

        if alert_duration_in_sec < 5:  # Si la durée de l'alerte est inférieure à 5 secondes
            # Calcul du nombre de frames supplémentaires à ajouter pour atteindre 7 secondes
            additional_duration_in_ms = (7 * 1000) - alert_duration_in_ms  # en millisecondes
            additional_frames = int(additional_duration_in_ms * fps / 1000)  # Nombre de frames à ajouter

            # Ajouter des frames avant et après la vidéo pour atteindre 7 secondes
            additional_frames_before = frames[:min(additional_frames, len(frames) // 2)]
            additional_frames_after = frames[-min(additional_frames, len(frames) // 2):]

            # Construire la nouvelle liste de frames prolongée
            frames = additional_frames_before + frames + additional_frames_after

        # Sauvegarde de la vidéo
        video_path = os.path.join(alert_dir, f"alert_{alert_id}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(video_path, fourcc, fps, frame_size)

        for frame in frames:
            out.write(frame)

        out.release()

        # Si WebSocket est actif, envoie les alertes
        if alert_data['websocket']:
            alert_data["video_path"] = video_path  # Ajout du chemin vidéo
            self.send_to_websocket(alert_data)  # Envoi des alertes via WebSocket

        print(f"Alerte sauvegardée : {json_path}, Vidéo : {video_path}")

    def detect_children(self, frame, results):
        """
        Détecte les personnes et identifie les enfants selon leur taille relative.
        """
        person_boxes = []
        children_boxes = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                label = int(box.cls[0].cpu().numpy())

                if label == 0 and confidence > 0.3:
                    height = y2 - y1
                    width = x2 - x1
                    person_boxes.append((x1, y1, x2, y2, height, width, confidence))

        avg_height = np.mean([box[4] for box in person_boxes]) if person_boxes else 0
        avg_width = np.mean([box[5] for box in person_boxes]) if person_boxes else 0

        for box in person_boxes:
            x1, y1, x2, y2, height, width, confidence = box
            if height < 0.7 * avg_height and width < 0.7 * avg_width:
                children_boxes.append((x1, y1, x2, y2, confidence))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                text = f"Enfant: {confidence:.2f}"
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return frame, children_boxes

    def process_video(self, video_path):
        """
        Traite une vidéo spécifique pour détecter les enfants et générer des alertes.
        """
        cap, frame_width, frame_height, fps = self.setup_video_io(video_path)
        frame_size = (frame_width, frame_height)

        print(f"Traitement de la vidéo {video_path} ...")
        alert_frames = {}

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame, conf=0.3, iou=0.4)
            frame, children_boxes = self.detect_children(frame, results)

            detections_for_sort = np.array([[x1, y1, x2, y2, conf] for x1, y1, x2, y2, conf in children_boxes])
            detections_for_sort = detections_for_sort if detections_for_sort.shape[0] > 0 else np.empty((0, 5))

            tracked_objects = self.tracker.update(detections_for_sort)

            for tracked in tracked_objects:
                x1, y1, x2, y2, obj_id = map(int, tracked)
                if obj_id not in self.alerted_ids:
                    alert_id = len(self.alerted_ids) + 1
                    date_heure = time.strftime("%Y-%m-%d %H:%M:%S").split()
                    alert_data = {
                        "id": alert_id,
                        "heure": date_heure[1],
                        "date": date_heure[0],
                        "camera": os.path.basename(video_path),
                        "statut": "en cours",
                        "video": f"alert_{alert_id}.mp4",
                        "Websocket": False,
                        "lastUpdate": "",
                        "UpdatedBy": "",
                        "fauxPositif": False
                    }
                    self.alerted_ids.add(obj_id)
                    alert_frames[obj_id] = {"data": alert_data, "frames": []}

                if obj_id in alert_frames:
                    alert_frames[obj_id]["frames"].append(frame.copy())

            cv2.imshow("Tracking des enfants", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Sauvegarde des alertes et vidéos
        for obj_id, alert in alert_frames.items():
            self.save_alert(alert["data"]["id"], alert["data"], alert["frames"], fps, frame_size)

        cap.release()
        cv2.destroyAllWindows()

    def watch_folder(self):
        """
        Surveillance d'un dossier pour détecter et traiter de nouvelles vidéos.
        """
        print(f"Surveillance du dossier {self.watch_dir} ...")
        processed_files = set()

        while True:
            current_files = set(os.listdir(self.watch_dir))
            new_files = current_files - processed_files

            for file in new_files:
                if file.endswith(".mp4"):
                    video_path = os.path.join(self.watch_dir, file)
                    self.process_video(video_path)
                    processed_files.add(file)

            time.sleep(2)


if __name__ == "__main__":
    # Paramètres de démarrage
    model_path = 'yolov11m.pt'
    watch_dir = './input_videos/'
    output_dir = 'E:/Pils/output'

    child_tracker = ChildTrackingSystem(model_path, watch_dir, output_dir)
    child_tracker.watch_folder()
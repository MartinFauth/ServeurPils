import cv2
import numpy as np
import torch
from ultralytics import YOLO
from sort import Sort
import os
import json
import time
from flask import Flask
from flask_socketio import SocketIO, emit

class ChildTrackingSystem:
    def __init__(self, model_path, watch_dir, output_dir):
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

        # Flask-SocketIO setup
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.clients_connected = 0  # Compteur de clients connectés

        # Configuration des gestionnaires SocketIO
        self.setup_socketio_handlers()

    def setup_socketio_handlers(self):
        """Configure les gestionnaires d'événements WebSocket."""
        @self.socketio.on('connect')
        def handle_connect():
            self.clients_connected += 1
            print(f"Client connecté. Total : {self.clients_connected}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.clients_connected -= 1
            print(f"Client déconnecté. Total : {self.clients_connected}")

        @self.socketio.on_error_default
        def default_error_handler(e):
            print(f"Erreur Socket.IO : {e}")


        @self.socketio.on('message')
        def handle_message(data):
            print(f"Message reçu du client : {data}")

    def setup_video_io(self, video_path):
        """Ouvre la vidéo d'entrée et retourne ses caractéristiques."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Erreur : Impossible d'ouvrir la vidéo {video_path}.")
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        return cap, frame_width, frame_height, fps

    def send_video_via_websocket(self, video_path, alert_data):
        """Envoie une vidéo via WebSocket si un client est connecté."""
        if self.clients_connected > 0:
            print(f"Envoi de la vidéo {video_path} via WebSocket...")
            with open(video_path, "rb") as video_file:
                video_data = video_file.read()
                self.socketio.emit('new_video', {"alert": alert_data, "video": video_data})
            print("Vidéo envoyée avec succès via WebSocket.")

    def save_alert(self, alert_id, alert_data, frames, fps, frame_size):
        """Sauvegarde une alerte sous forme de fichier JSON et extrait une vidéo correspondante."""
        alert_dir = os.path.join(self.output_dir, "alerts")
        if not os.path.exists(alert_dir):
            os.makedirs(alert_dir)

        json_path = os.path.join(alert_dir, f"alert_{alert_id}.json")
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(alert_data, json_file, indent=4, ensure_ascii=False)

        video_path = os.path.join(alert_dir, alert_data["video"])
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"Alerte sauvegardée : {json_path}, Vidéo : {video_path}")

        if self.clients_connected > 0:
            self.send_video_via_websocket(video_path, alert_data)

    def process_video(self, video_path):
        """Traite une vidéo spécifique pour détecter les enfants."""
        cap, frame_width, frame_height, fps = self.setup_video_io(video_path)
        frame_size = (frame_width, frame_height)
        print(f"Traitement de la vidéo {video_path} ...")
        alert_frames = {}
        all_frames = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, frame_size)
                results = self.model(frame, conf=0.3, iou=0.4)
                frame, children_boxes = self.detect_children(frame, results)
                all_frames.append(frame.copy())
        finally:
            cap.release()

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

    def watch_folder(self):
        """Surveillance d'un dossier pour détecter de nouvelles vidéos."""
        print(f"Surveillance du dossier {self.watch_dir} ...")
        while True:
            for file in os.listdir(self.watch_dir):
                if file.endswith(".mp4"):
                    video_path = os.path.join(self.watch_dir, file)
                    self.process_video(video_path)
            time.sleep(2)

    def run(self):
        """Lance le serveur WebSocket et la surveillance des vidéos."""
        print("Démarrage du serveur WebSocket...")
        self.socketio.start_background_task(self.watch_folder)
        self.socketio.run(self.app, host="127.0.0.1", port=5050)


if __name__ == "__main__":
    model_path = "yolo11m.pt"
    watch_dir = "./input_videos/"
    output_dir = "E:/Pils/output_videos/"
    system = ChildTrackingSystem(model_path, watch_dir, output_dir)
    system.run()

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from sort import Sort
import os
import json
import time
import requests
from flask import Flask

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

        # Flask App
        self.app = Flask(__name__)

    def setup_video_io(self, video_path):
        """
        Ouvre la vidéo d'entrée et retourne ses caractéristiques.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Erreur : Impossible d'ouvrir la vidéo {video_path}.")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        return cap, frame_width, frame_height, fps

    def save_alert(self, alert_data, frames, fps, frame_size):
        """
        Ajoute une alerte à la base de données via l'API et sauvegarde la vidéo localement.
        """
        # Sauvegarde de la vidéo localement
        alert_dir = os.path.join(self.output_dir, "alerts")
        if not os.path.exists(alert_dir):
            os.makedirs(alert_dir)

        video_path = os.path.join(alert_dir, alert_data["video"])
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(video_path, fourcc, fps, frame_size)

        for frame in frames:
            out.write(frame)

        out.release()
        print(f"Vidéo sauvegardée localement : {video_path}")

        # Envoi des données d'alerte à l'API
        api_url = "http://127.0.0.1:5001/api/alertes"
        try:
            response = requests.post(api_url, json=alert_data)
            if response.status_code == 201:
                print(f"Alerte ajoutée avec succès : {alert_data}")
            else:
                print(f"Erreur lors de l'ajout de l'alerte : {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception lors de l'envoi de l'alerte : {e}")

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
        Traite une vidéo spécifique pour détecter les enfants, générer des alertes et inclure le tracking dans les vidéos d'alertes.
        """
        cap, frame_width, frame_height, fps = self.setup_video_io(video_path)
        frame_size = (frame_width, frame_height)
        all_frames = []

        print(f"Traitement de la vidéo {video_path} ...")

        try:
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
                            "heure": date_heure[1],
                            "date": date_heure[0],
                            "camera_id": 2,##os.path.basename(video_path),
                            "statut": "en cours",
                            "video": f"alert_{alert_id}.mp4",
                            "websocket": 0,
                            "lastUpdate": date_heure[1],
                            "updatedBy": "system",
                            "fauxPositif": False
                        }
                        self.alerted_ids.add(obj_id)

                        # Sauvegarder l'alerte et la vidéo localement
                        self.save_alert(alert_data, all_frames, fps, frame_size)

                all_frames.append(frame.copy())

                cv2.imshow("Tracking des enfants", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
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

    def run(self):
        """
        Lance le traitement des vidéos.
        """
        print("Démarrage de la surveillance des vidéos...")
        self.watch_folder()

if __name__ == "__main__":
    # Paramètres
    model_path = "yolo11m.pt"
    watch_dir = "./input_videos/"
    output_dir = "E:/Pils/output_videos/"

    system = ChildTrackingSystem(model_path, watch_dir, output_dir)
    system.run()

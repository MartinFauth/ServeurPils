import cv2
import numpy as np
import torch
from ultralytics import YOLO
from sort import Sort
import os
import json
import time
import asyncio
import websockets
import base64


class ChildTrackingSystem:
    def __init__(self, model_path, watch_dir, output_dir):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Appareil utilisé : {self.device}")
        self.model = YOLO(model_path)
        self.watch_dir = watch_dir
        self.output_dir = output_dir
        self.alerted_ids = set()
        self.tracker = Sort(max_age=30, min_hits=3, iou_threshold=0.2)
        self.clients = set()

    async def websocket_handler(self, websocket, path):
        """
        Gestionnaire pour les connexions WebSocket.
        """
        print(f"Nouvelle connexion WebSocket sur le chemin: {path}")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                print(f"Message reçu : {message}")
        except Exception as e:
            print(f"Erreur WebSocket : {e}")
        finally:
            self.clients.remove(websocket)
            print("Client déconnecté.")

    async def broadcast_alert(self, alert_data, video_path):
        """Diffuse les alertes et vidéos à tous les clients connectés."""
        if self.clients:
            print(f"Envoi de l'alerte {alert_data['id']} à {len(self.clients)} clients...")
            with open(video_path, "rb") as video_file:
                video_data = base64.b64encode(video_file.read()).decode("utf-8")
                alert_message = {
                    "alert": alert_data,
                    "video": video_data
                }
                message = json.dumps(alert_message)
                await asyncio.gather(*[client.send(message) for client in self.clients])
            print("Alerte envoyée avec succès.")

    async def watch_folder(self):
        """Surveillance d'un dossier pour détecter et traiter de nouvelles vidéos."""
        print(f"Surveillance du dossier {self.watch_dir} ...")
        processed_files = set()
        while True:
            current_files = set(os.listdir(self.watch_dir))
            new_files = current_files - processed_files
            for file in new_files:
                if file.endswith(".mp4"):
                    video_path = os.path.join(self.watch_dir, file)
                    await self.process_video(video_path)
                    processed_files.add(file)
            await asyncio.sleep(2)

    async def process_video(self, video_path):
        """Traite une vidéo spécifique pour détecter les enfants et générer des alertes."""
        cap, frame_width, frame_height, fps = self.setup_video_io(video_path)
        frame_size = (frame_width, frame_height)
        min_duration_frames = int(10 * fps)  # Nombre de frames pour 10 secondes
        print(f"Traitement de la vidéo {video_path} ...")
        alert_frames = {}
        all_frames = []
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame.shape[1] != frame_width or frame.shape[0] != frame_height:
                    frame = cv2.resize(frame, frame_size)
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
                        alert_frames[obj_id] = {"data": alert_data, "frames": [], "start_frame": len(all_frames)}
                    if obj_id in alert_frames:
                        alert_frames[obj_id]["frames"].append(frame.copy())
                all_frames.append(frame.copy())
        finally:
            cap.release()
            for obj_id, alert in alert_frames.items():
                alert_id = alert["data"]["id"]
                frames = alert["frames"]
                video_path = self.save_alert(alert_id, alert["data"], frames, fps, frame_size)
                await self.broadcast_alert(alert["data"], video_path)

    def detect_children(self, frame, results):
        """Détecte les personnes et identifie les enfants selon leur taille relative."""
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
                cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        return frame, children_boxes

    def setup_video_io(self, video_path):
        """Ouvre la vidéo d'entrée et retourne ses caractéristiques."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Erreur : Impossible d'ouvrir la vidéo {video_path}.")
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        return cap, frame_width, frame_height, fps

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
        return video_path

    def run(self):
        """
        Lance le serveur WebSocket et le traitement des vidéos.
        """
        print("Démarrage du serveur WebSocket...")

        async def start_server():
            server = await websockets.serve(self.websocket_handler, "127.0.0.1", 8765)
            print("Serveur WebSocket démarré sur ws://127.0.0.1:8765")
            await asyncio.gather(server.wait_closed(), self.watch_folder())

        asyncio.run(start_server())


if __name__ == "__main__":
    model_path = "yolo11m.pt"
    watch_dir = "./input_videos/"
    output_dir = "E:/Pils/output_videos/"

    system = ChildTrackingSystem(model_path, watch_dir, output_dir)
    system.run()

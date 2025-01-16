from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, path ='/')

@socketio.on('connect')
def handle_connect():
    print("Client connecté.")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client déconnecté.")

@socketio.on('message')
def handle_message(data):
    print(f"Message reçu du client : {data}")
    socketio.emit('response', {"message": "Message reçu avec succès !"})

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=8765, debug=True)

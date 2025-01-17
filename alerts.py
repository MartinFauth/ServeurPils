from flask import Flask, jsonify, request, Response, abort
from flask_mysqldb import MySQL
from datetime import datetime, date, timedelta
import decimal
from flask_cors import CORS
import os




app = Flask(__name__)


# Configuration de la connexion MySQL
app.config['MYSQL_HOST'] = 'localhost'  # Remplacer par ton hôte MySQL
app.config['MYSQL_USER'] = 'root'  # Remplacer par ton utilisateur MySQL
app.config['MYSQL_PASSWORD'] = 'Admin'  # Remplacer par ton mot de passe MySQL
app.config['MYSQL_DB'] = 'alerts_list'
CORS(app, supports_credentials=True)

mysql = MySQL(app)


# Fonction utilitaire pour convertir les types non JSON-sérialisables
def serialize_sql_row(row):
    result = {}
    columns = ('id', 'heure', 'date', 'camera_id', 'statut', 'video', 'websocket', 'lastUpdate', 'updatedBy', 'fauxPositif')
    for key, value in zip(columns, row):
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()  # Convertir en format ISO 8601
        elif isinstance(value, timedelta):
            result[key] = value.total_seconds()  # Convertir en total de secondes
        elif isinstance(value, decimal.Decimal):
            result[key] = float(value)  # Convertir en float
        else:
            result[key] = value
    return result

@app.route('/api/alertes', methods=['GET'])
def get_alertes():
    # Récupérer tous les paramètres de la requête
    filters = request.args.to_dict()

    # Construction dynamique de la requête SQL
    query = "SELECT * FROM alerts_list WHERE 1=1"
    query_params = []

    # Ajouter les conditions en fonction des attributs présents dans la requête
    for column, value in filters.items():
        query += f" AND {column} = %s"
        query_params.append(value)

    cur = mysql.connection.cursor()
    cur.execute(query, query_params)  # Utilisation de paramètres pour éviter les injections SQL
    alertes = cur.fetchall()

    # Sérialisation des résultats
    result = [serialize_sql_row(alerte) for alerte in alertes]

    return jsonify(result)


@app.route('/api/alertes/<int:id>', methods=['PUT'])
def update_alerte(id):
    data = request.get_json()
    heure = data.get('heure')
    date = data.get('date')
    camera_id = data.get('camera_id')
    statut = data.get('statut')
    video = data.get('video')
    websocket = data.get('websocket')
    lastUpdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updatedBy = data.get('updatedBy')
    fauxPositif = data.get('fauxPositif', False)

    query = """
    UPDATE alerts_list
    SET heure = %s, date = %s, camera_id = %s, statut = %s, video = %s, websocket = %s,
        lastUpdate = %s, updatedBy = %s, fauxPositif = %s
    WHERE id = %s
    """
    
    cur = mysql.connection.cursor()
    cur.execute(query, (heure, date, camera_id, statut, video, websocket, lastUpdate, updatedBy, fauxPositif, id))
    mysql.connection.commit()
    return jsonify({"message": "Alerte mise à jour avec succès"})

@app.route('/api/alertes/all', methods=['GET'])
def get_all_alertes():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM alerts_list")
    alertes = cur.fetchall()
    result = [serialize_sql_row(alerte) for alerte in alertes]
    return jsonify(result)

@app.route('/api/alertes', methods=['POST'])
def add_alerte():
    data = request.get_json()
    heure = data.get('heure')
    date = data.get('date')
    camera_id = data.get('camera_id')
    statut = data.get('statut')
    video = data.get('video', None)
    websocket = data.get('websocket', None)
    lastUpdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updatedBy = data.get('updatedBy', 'unknown')
    fauxPositif = data.get('fauxPositif', False)

    query = """
    INSERT INTO alerts_list (heure, date, camera_id, statut, video, websocket, lastUpdate, updatedBy, fauxPositif)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cur = mysql.connection.cursor()
    cur.execute(query, (heure, date, camera_id, statut, video, websocket, lastUpdate, updatedBy, fauxPositif))
    mysql.connection.commit()
    
    return jsonify({"message": "Alerte ajoutée avec succès"}), 201

# Chemin absolu vers le dossier contenant les vidéos
VIDEO_FOLDER = "E:/Pils/output_videos/alerts"

@app.route('/videos/<filename>')
def stream_video(filename):
    # Chemin complet de la vidéo
    video_path = os.path.join(VIDEO_FOLDER, filename)

    # Vérifier si le fichier existe
    if not os.path.exists(video_path):
        abort(404, "Vidéo introuvable")

    # Obtenir l'en-tête "Range" de la requête
    range_header = request.headers.get('Range', None)
    file_size = os.path.getsize(video_path)
    print("range headear ========================        " , range_header)
    # Si aucun en-tête Range n'est fourni, envoyer le fichier complet
    if range_header is None:
        return Response(
            open(video_path, "rb"),
            status=200,
            headers={
                "Content-Length": file_size,
                "Accept-Ranges": "bytes",
                "Content-Type": "video/mp4",
            },
        )

    # Analyser l'en-tête Range
    try:
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0])
        end = int(range_match[1]) if range_match[1] else file_size - 1
    except ValueError:
        abort(400, "En-tête Range invalide")

    # Limiter la fin à la taille totale du fichier
    end = min(end, file_size - 1)
    chunk_size = end - start + 1

    # Lire la portion demandée
    with open(video_path, "rb") as f:
        f.seek(start)
        chunk_data = f.read(chunk_size)

    # Construire la réponse
    response = Response(
        chunk_data,
        status=206,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": chunk_size,
            "Content-Type": "video/mp4",
        },
    )
    return response








if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001)



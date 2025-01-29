import subprocess

# Lancer l'application auth (API d'authentification sur le port 5001)
subprocess.Popen(["python", "auth.py"])

# Lancer l'application alertes (API des alertes sur le port 5000)
subprocess.Popen(["python", "alerts.py"])

# Lancer fusionSansWS.py
#subprocess.Popen(["python", "fusionSansWS.py"])


##subprocess.Popen(["python", "sockettest.py"])

# Empêcher le script de se fermer immédiatement et maintenir les processus actifs
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Arrêt du launcher.")

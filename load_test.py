"""Envoie une série de messages réalistes à ChocoBot (serveur lancé sur le port 8000).
Usage : python load_test.py [nombre_de_conversations]   (défaut : 2, soit 10 messages)
Avec un vrai LLM chaque message prend plusieurs secondes : commencez petit."""
import json, sys, urllib.request

BASE = "http://localhost:8000"
SCENARIO = [
    "Quels sont vos horaires ?",
    "Je cherche un coffret pour 30 euros, mon fils est allergique aux noisettes.",
    "Et pour les enfants, vous avez quoi ?",
    "Quels sont vos horaires ?",
    "Merci, je prends le coffret sans noix !",
]
# Informations transmises avec chaque message, jamais stockées côté serveur.
PROFILE = {"name": "", "email": "", "allergies": "noisettes", "children_ages": "7-10 ans"}


def post(path, payload):
    req = urllib.request.Request(BASE + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
for i in range(n):
    for msg in SCENARIO:
        post("/chat", {"message": msg, "profile": PROFILE})
print(f"{n * len(SCENARIO)} messages envoyés.")

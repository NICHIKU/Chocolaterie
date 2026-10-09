import base64
import os
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from chatbot import handle_chat
import db  # purge les tables héritées au démarrage : rien n'est stocké
import llm

app = FastAPI(title="ChocoBot - Maison Delcourt")
app.mount("/static", StaticFiles(directory="static"), name="static")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "delcourt")


class Profile(BaseModel):
    """Informations saisies par le client : transmises avec le message, jamais conservées."""
    name: str = ""
    email: str = ""
    allergies: str = ""
    children_ages: str = ""


class ChatIn(BaseModel):
    message: str
    profile: Profile = Profile()


def is_admin(request: Request) -> bool:
    """Vérifie les identifiants envoyés à chaque requête : aucune session conservée côté serveur."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
    except Exception:
        return False
    username, _, password = decoded.partition(":")
    user_ok = secrets.compare_digest(username.encode("utf-8"), ADMIN_USER.encode("utf-8"))
    password_ok = secrets.compare_digest(password.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8"))
    return user_ok and password_ok


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/chat")
def chat(body: ChatIn):
    return handle_chat(body.message, body.profile.model_dump())


# Back-office de l'équipe Delcourt : aucun client, aucun message n'y figure.
# /admin affiche toujours le formulaire ; seules les données sont protégées,
# sans header WWW-Authenticate pour ne jamais déclencher la popup du navigateur.
@app.get("/admin")
def admin():
    return FileResponse("static/admin.html")


@app.get("/admin/data")
def admin_data(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="Authentification requise")
    return {"llm": {"big": llm.BIG_MODEL, "small": llm.SMALL_MODEL}}


@app.get("/health")
def health():
    return {"status": "ok"}

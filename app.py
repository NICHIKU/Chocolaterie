import os
import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from chatbot import handle_chat
import db
import llm

app = FastAPI(title="ChocoBot - Maison Delcourt")
app.mount("/static", StaticFiles(directory="static"), name="static")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "delcourt")
basic_security = HTTPBasic()


class ChatIn(BaseModel):
    session_id: str
    message: str


class SessionIn(BaseModel):
    session_id: str


class ProfileIn(BaseModel):
    session_id: str
    name: str = ""
    email: str = ""
    allergies: str = ""
    children_ages: str = ""


def require_admin(credentials: HTTPBasicCredentials = Depends(basic_security)):
    """Accès réservé à l'équipe Delcourt : HTTP Basic sur /admin et /admin/data."""
    user_ok = secrets.compare_digest(credentials.username.encode("utf-8"), ADMIN_USER.encode("utf-8"))
    password_ok = secrets.compare_digest(credentials.password.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8"))
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": 'Basic realm="ChocoBot Back-office"'},
        )


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/profile")
def profile(body: ProfileIn):
    db.save_customer(body.session_id, body.name, body.email, body.allergies, body.children_ages)
    return {"status": "saved"}


@app.post("/chat")
def chat(body: ChatIn):
    return handle_chat(body.session_id, body.message)


# Fin de conversation : on efface l'historique des messages de cette session
@app.post("/chat/end")
def chat_end(body: SessionIn):
    db.clear_history(body.session_id)
    return {"status": "cleared"}


# Back-office de l'équipe Delcourt : pratique pour voir qui a écrit quoi
@app.get("/admin")
def admin(credentials: HTTPBasicCredentials = Depends(require_admin)):
    return FileResponse("static/admin.html")


@app.get("/admin/data")
def admin_data(credentials: HTTPBasicCredentials = Depends(require_admin)):
    data = db.get_all()
    data["llm"] = {"big": llm.BIG_MODEL, "small": llm.SMALL_MODEL}
    return data


@app.get("/health")
def health():
    return {"status": "ok"}

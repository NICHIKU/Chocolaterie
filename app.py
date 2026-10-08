from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from chatbot import handle_chat
import db
import llm

app = FastAPI(title="ChocoBot - Maison Delcourt")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatIn(BaseModel):
    session_id: str
    message: str


class ProfileIn(BaseModel):
    session_id: str
    name: str = ""
    email: str = ""
    allergies: str = ""
    children_ages: str = ""


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


# Back-office de l'équipe Delcourt : pratique pour voir qui a écrit quoi
@app.get("/admin")
def admin():
    return FileResponse("static/admin.html")


@app.get("/admin/data")
def admin_data():
    data = db.get_all()
    data["llm"] = {"big": llm.BIG_MODEL, "small": llm.SMALL_MODEL}
    return data


@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import sqlite3
import os
from typing import List

app = FastAPI()


# Ścieżka do frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")

print("Frontend DIR:", FRONTEND_DIR)
print("index.html exists?", os.path.exists(os.path.join(FRONTEND_DIR, "index.html")))
print("login.html exists?", os.path.exists(os.path.join(FRONTEND_DIR, "login.html")))

# Serwowanie statycznych plików JS/CSS
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# -----------------------------
# Strony HTML
# -----------------------------
@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/login")
def login_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/register")
def register_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))

@app.get("/dashboard")
def dashboard_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

# -----------------------------
# Baza danych
# -----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)""")
c.execute("""CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    city TEXT
)""")
conn.commit()

# Modele danych
class User(BaseModel):
    username: str
    password: str

class HistoryItem(BaseModel):
    city: str

# -----------------------------
# API
# -----------------------------
@app.post("/api/register")
def register(user: User):
    hashed = pwd_context.hash(user.password)
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, hashed))
        conn.commit()
        return {"message": "Zarejestrowano pomyślnie"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Użytkownik już istnieje")

@app.post("/api/login")
def login(user: User):
    c.execute("SELECT password FROM users WHERE username=?", (user.username,))
    row = c.fetchone()
    if not row or not pwd_context.verify(user.password, row[0]):
        raise HTTPException(status_code=401, detail="Nieprawidłowy login lub hasło")
    return {"username": user.username}

@app.post("/api/history/{username}")
def add_history(username: str, item: HistoryItem):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    user_id = row[0]
    c.execute("INSERT INTO history (user_id, city) VALUES (?, ?)", (user_id, item.city))
    conn.commit()
    return {"message": "Dodano do historii"}

@app.get("/api/history/{username}", response_model=List[HistoryItem])
def get_history(username: str):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    user_id = row[0]
    c.execute("SELECT city FROM history WHERE user_id=? ORDER BY id DESC", (user_id,))
    cities = c.fetchall()
    return [{"city": city[0]} for city in cities]

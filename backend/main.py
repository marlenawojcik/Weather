from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import sqlite3
import os
from typing import List
from fastapi import FastAPI, HTTPException, Response

app = FastAPI()


# Ścieżka do frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")



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

    response = JSONResponse(content={"message": "Zalogowano pomyślnie",
                                        "username": user.username})
    response.set_cookie(
        key="username",
        value=user.username,
        httponly=False,   #False, żeby JS mógł odczytać cookie
        samesite="lax"
    )
    return response


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


#ustaw domysle miasto
@app.post("/api/default_city/{username}")
def set_default_city(username: str, item: HistoryItem):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    user_id = row[0]
    # Dodaj kolumnę default_city jeśli nie istnieje
    c.execute("ALTER TABLE users ADD COLUMN default_city TEXT") if "default_city" not in [col[1] for col in c.execute("PRAGMA table_info(users)").fetchall()] else None
    c.execute("UPDATE users SET default_city=? WHERE id=?", (item.city, user_id))
    conn.commit()
    return {"message": f"Ustawiono domyślne miasto na {item.city}"}

#pobierz najczesciej wyszukiwane miasta
@app.get("/api/top_cities/{username}")
def get_top_cities(username: str, limit: int = 5):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    user_id = row[0]
    c.execute("""
        SELECT city, COUNT(*) as count 
        FROM history 
        WHERE user_id=? 
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT ?
    """, (user_id, limit))
    cities = c.fetchall()
    return [city[0] for city in cities]

# 🔹 Usuń historię
@app.delete("/api/history/{username}")
def delete_history(username: str):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    user_id = row[0]
    c.execute("DELETE FROM history WHERE user_id=?", (user_id,))
    conn.commit()
    return {"message": "Historia została usunięta"}


# 🔹 Usuń konto
@app.delete("/api/user/{username}")
def delete_user(username: str):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    user_id = row[0]
    c.execute("DELETE FROM history WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    return {"message": "Konto zostało usunięte"}
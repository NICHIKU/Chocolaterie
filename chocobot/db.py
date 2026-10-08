import sqlite3, time

conn = sqlite3.connect("chocobot.db", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS customers (
    session_id TEXT PRIMARY KEY, name TEXT, email TEXT, allergies TEXT, children_ages TEXT, created_at REAL)""")
conn.execute("""CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, created_at REAL)""")
conn.commit()


def save_customer(session_id, name, email, allergies, children_ages):
    conn.execute("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)",
                 (session_id, name, email, allergies, children_ages, time.time()))
    conn.commit()


def get_customer(session_id):
    row = conn.execute("SELECT name, email, allergies, children_ages FROM customers WHERE session_id=?",
                       (session_id,)).fetchone()
    return dict(zip(["name", "email", "allergies", "children_ages"], row)) if row else {}


def save_message(session_id, role, content):
    conn.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
                 (session_id, role, content, time.time()))
    conn.commit()


def get_history(session_id):
    rows = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    return [{"role": r, "content": c} for r, c in rows]


def get_all():
    cust = conn.execute("SELECT session_id, name, email, allergies, children_ages, created_at FROM customers ORDER BY created_at DESC").fetchall()
    msgs = conn.execute("SELECT id, session_id, role, content, created_at FROM messages ORDER BY id DESC LIMIT 200").fetchall()
    return {
        "customers": [dict(zip(["session_id", "name", "email", "allergies", "children_ages", "created_at"], r)) for r in cust],
        "messages": [dict(zip(["id", "session_id", "role", "content", "created_at"], r)) for r in msgs],
    }

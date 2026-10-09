import sqlite3, time

conn = sqlite3.connect("chocobot.db", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS customers (
    session_id TEXT PRIMARY KEY, name TEXT, email TEXT, allergies TEXT, children_ages TEXT, created_at REAL)""")
# Aucun historique de conversation n'est conservé : on purge la table messages si elle existe encore.
conn.execute("DROP TABLE IF EXISTS messages")
conn.commit()


def save_customer(session_id, name, email, allergies, children_ages):
    conn.execute("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)",
                 (session_id, name, email, allergies, children_ages, time.time()))
    conn.commit()


def get_customer(session_id):
    row = conn.execute("SELECT name, email, allergies, children_ages FROM customers WHERE session_id=?",
                       (session_id,)).fetchone()
    return dict(zip(["name", "email", "allergies", "children_ages"], row)) if row else {}


def get_all():
    cust = conn.execute("SELECT session_id, name, email, allergies, children_ages, created_at FROM customers ORDER BY created_at DESC").fetchall()
    return {
        "customers": [dict(zip(["session_id", "name", "email", "allergies", "children_ages", "created_at"], r)) for r in cust],
    }

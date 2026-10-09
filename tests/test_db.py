import sqlite3

import db


def make_legacy_db(tmp_path):
    """Base héritée : une fiche client + un historique de messages."""
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE customers (session_id TEXT PRIMARY KEY, name TEXT, email TEXT)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT)")
    conn.execute("INSERT INTO customers VALUES ('s1', 'Léa', 'lea@example.com')")
    conn.execute("INSERT INTO messages VALUES (1, 'bonjour')")
    conn.commit()
    conn.close()
    return str(path)


def tables(db_path):
    conn = sqlite3.connect(db_path)
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    return names


def test_purge_drops_legacy_tables_and_rows(tmp_path):
    path = make_legacy_db(tmp_path)

    db.purge(path)

    assert tables(path) == set()


def test_purge_is_safe_on_a_missing_or_empty_database(tmp_path):
    path = str(tmp_path / "vide.db")

    db.purge(path)
    db.purge(path)  # deux purges d'affilée : aucune erreur, aucune table

    assert tables(path) == set()


def test_db_exposes_no_storage_at_all():
    """db.py ne doit avoir ni écriture ni lecture de données utilisateur."""
    for name in ["save_customer", "get_customer", "get_all", "save_message", "get_history", "clear_history"]:
        assert not hasattr(db, name), f"db.{name} ne doit plus exister"


def test_startup_purge_left_no_legacy_table_in_the_real_database():
    """Le purgeur exécuté à l'import a bien vidé chocobot.db (le fichier est conservé, vide)."""
    assert tables("chocobot.db") & {"customers", "messages"} == set()

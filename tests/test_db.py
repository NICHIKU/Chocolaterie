import db


class FakeConn:
    """Faux objet connexion : enregistre les requêtes SQL et renvoie des réponses programmées."""

    def __init__(self, fetchone_result=None, fetchall_results=None):
        self.calls = []
        self.commits = 0
        self.fetchone_result = fetchone_result
        self.fetchall_results = list(fetchall_results or [])

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []

    def commit(self):
        self.commits += 1


def fake_conn(monkeypatch, **kwargs):
    conn = FakeConn(**kwargs)
    monkeypatch.setattr(db, "conn", conn)
    return conn


def test_save_customer_executes_insert_and_commits(monkeypatch):
    conn = fake_conn(monkeypatch)
    monkeypatch.setattr(db.time, "time", lambda: 1_700_000_000.0)

    db.save_customer("s1", "Léa", "lea@example.com", "noisettes", "6 ans")

    assert conn.calls == [
        (
            "INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)",
            ("s1", "Léa", "lea@example.com", "noisettes", "6 ans", 1_700_000_000.0),
        )
    ]
    assert conn.commits == 1


def test_get_customer_maps_row_to_dict(monkeypatch):
    conn = fake_conn(monkeypatch, fetchone_result=("Léa", "lea@example.com", "noisettes", "4-6 ans"))

    assert db.get_customer("s1") == {
        "name": "Léa",
        "email": "lea@example.com",
        "allergies": "noisettes",
        "children_ages": "4-6 ans",
    }
    sql, params = conn.calls[0]
    assert "WHERE session_id=?" in sql
    assert "name, email, allergies, children_ages" in sql
    assert params == ("s1",)


def test_get_unknown_customer_returns_empty_dict(monkeypatch):
    conn = fake_conn(monkeypatch, fetchone_result=None)

    assert db.get_customer("inconnu") == {}
    assert conn.calls  # la requête est bien exécutée même sans ligne


def test_db_exposes_no_message_persistence():
    """Aucune écriture ni lecture d'historique de conversation dans SQLite."""
    for name in ["save_message", "get_history", "clear_history"]:
        assert not hasattr(db, name), f"db.{name} ne doit plus exister"


def test_get_all_returns_only_customers(monkeypatch):
    conn = fake_conn(
        monkeypatch,
        fetchall_results=[
            [("s1", "Léa", "lea@example.com", "noisettes", "6 ans", 1.0)],
        ],
    )

    data = db.get_all()

    assert data == {
        "customers": [
            {
                "session_id": "s1",
                "name": "Léa",
                "email": "lea@example.com",
                "allergies": "noisettes",
                "children_ages": "6 ans",
                "created_at": 1.0,
            }
        ],
    }
    assert "messages" not in data
    assert len(conn.calls) == 1
    assert "ORDER BY created_at DESC" in conn.calls[0][0]

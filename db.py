import sqlite3

# Aucune donnée utilisateur n'est stockée : ce module ne fait que purger
# les tables héritées (historique et fiches clients) au démarrage.
LEGACY_TABLES = ("messages", "customers")


def purge(db_path="chocobot.db"):
    conn = sqlite3.connect(db_path)
    for table in LEGACY_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()


purge()

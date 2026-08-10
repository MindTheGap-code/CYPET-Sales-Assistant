from pathlib import Path
import sqlite3


class Database:
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent
        self.db_folder = project_root / "database"
        self.db_folder.mkdir(parents=True, exist_ok=True)

        self.db_path = self.db_folder / "csa.db"

        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        self.create_tables()

    # -------------------------------------------------
    # CREAZIONE TABELLE
    # -------------------------------------------------

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                outlook_id TEXT UNIQUE,
                sent_date TEXT,
                recipient_name TEXT,
                recipient_email TEXT,
                domain TEXT,
                subject TEXT
            )
        """)

        self.connection.commit()

    # -------------------------------------------------
    # INSERIMENTO EMAIL
    # -------------------------------------------------

    def insert_email(
        self,
        outlook_id,
        sent_date,
        recipient_name,
        recipient_email,
        domain,
        subject,
    ):
        try:
            self.cursor.execute("""
                INSERT INTO emails (
                    outlook_id,
                    sent_date,
                    recipient_name,
                    recipient_email,
                    domain,
                    subject
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                outlook_id,
                sent_date,
                recipient_name,
                recipient_email,
                domain,
                subject,
            ))

            self.connection.commit()
            return True

        except sqlite3.IntegrityError:
            return False

    # -------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------

    def total_emails(self):
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM emails
        """)

        return self.cursor.fetchone()[0]

    def total_domains(self):
        self.cursor.execute("""
            SELECT COUNT(DISTINCT domain)
            FROM emails
            WHERE domain <> ''
        """)

        return self.cursor.fetchone()[0]

    def last_email(self):
        self.cursor.execute("""
            SELECT MAX(sent_date)
            FROM emails
        """)

        row = self.cursor.fetchone()
        return row[0]

    # -------------------------------------------------
    # REPORT
    # -------------------------------------------------

    def get_domains(self):
        self.cursor.execute("""
            SELECT
                domain,
                COUNT(*) AS total,
                MAX(sent_date) AS last_contact
            FROM emails
            WHERE domain <> ''
            GROUP BY domain
            ORDER BY total DESC
        """)

        return self.cursor.fetchall()

    # -------------------------------------------------
    # CONNECTION
    # -------------------------------------------------

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

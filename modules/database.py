from pathlib import Path
import sqlite3
from datetime import datetime, timezone


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

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                company_name TEXT DEFAULT '',
                industry TEXT DEFAULT '',
                status TEXT DEFAULT 'New',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.connection.commit()

        # Create prospect records automatically for domains already
        # present in the email database.
        self._sync_domains_to_prospects()

    def _sync_domains_to_prospects(self):
        self.cursor.execute("""
            SELECT DISTINCT domain
            FROM emails
            WHERE domain <> ''
        """)

        domains = self.cursor.fetchall()
        now = self._now()

        for row in domains:
            self.cursor.execute("""
                INSERT OR IGNORE INTO prospects (
                    domain,
                    company_name,
                    industry,
                    status,
                    notes,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, '', 'New', '', ?, ?)
            """, (
                row["domain"],
                row["domain"],
                now,
                now,
            ))

        self.connection.commit()

    # -------------------------------------------------
    # EMAIL
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

            if domain:
                self._ensure_prospect(domain)

            return True

        except sqlite3.IntegrityError:
            return False

    # -------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------

    def total_emails(self):
        self.cursor.execute("SELECT COUNT(*) FROM emails")
        return self.cursor.fetchone()[0]

    def total_domains(self):
        self.cursor.execute("""
            SELECT COUNT(DISTINCT domain)
            FROM emails
            WHERE domain <> ''
        """)
        return self.cursor.fetchone()[0]

    def last_email(self):
        self.cursor.execute("SELECT MAX(sent_date) FROM emails")
        row = self.cursor.fetchone()
        return row[0]

    def get_recent_emails(self, limit=5):
        self.cursor.execute("""
            SELECT
                recipient_name,
                recipient_email,
                domain,
                subject,
                sent_date
            FROM emails
            ORDER BY sent_date DESC
            LIMIT ?
        """, (limit,))

        return self.cursor.fetchall()

    def get_domains(self, limit=5):
        self.cursor.execute("""
            SELECT
                domain,
                COUNT(*) AS total,
                MAX(sent_date) AS last_contact
            FROM emails
            WHERE domain <> ''
            GROUP BY domain
            ORDER BY last_contact DESC
            LIMIT ?
        """, (limit,))

        return self.cursor.fetchall()

    # -------------------------------------------------
    # PROSPECTS
    # -------------------------------------------------

    def _ensure_prospect(self, domain):
        if not domain:
            return

        now = self._now()

        self.cursor.execute("""
            INSERT OR IGNORE INTO prospects (
                domain,
                company_name,
                industry,
                status,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, '', 'New', '', ?, ?)
        """, (
            domain,
            domain,
            now,
            now,
        ))

        self.connection.commit()

    def total_prospects(self):
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM prospects
        """)
        return self.cursor.fetchone()[0]

    def get_prospects(self, search="", status="All statuses", industry="All industries"):
        query = """
            SELECT
                p.id,
                p.domain,
                p.company_name,
                p.industry,
                p.status,
                p.notes,
                p.created_at,
                p.updated_at,
                COUNT(e.id) AS contacts,
                MAX(e.sent_date) AS last_contact
            FROM prospects p
            LEFT JOIN emails e
                ON e.domain = p.domain
            WHERE 1=1
        """

        params = []

        if search:
            query += """
                AND (
                    LOWER(p.domain) LIKE ?
                    OR LOWER(p.company_name) LIKE ?
                )
            """
            value = f"%{search.lower()}%"
            params.extend([value, value])

        if status and status != "All statuses":
            query += " AND p.status = ?"
            params.append(status)

        if industry and industry != "All industries":
            query += " AND p.industry = ?"
            params.append(industry)

        query += """
            GROUP BY
                p.id,
                p.domain,
                p.company_name,
                p.industry,
                p.status,
                p.notes,
                p.created_at,
                p.updated_at
            ORDER BY
                last_contact DESC,
                p.domain ASC
        """

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_prospect(self, prospect_id):
        self.cursor.execute("""
            SELECT *
            FROM prospects
            WHERE id = ?
        """, (prospect_id,))

        return self.cursor.fetchone()

    def save_prospect(
        self,
        prospect_id,
        company_name,
        industry,
        status,
        notes,
    ):
        now = self._now()

        self.cursor.execute("""
            UPDATE prospects
            SET
                company_name = ?,
                industry = ?,
                status = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            company_name.strip(),
            industry.strip(),
            status.strip(),
            notes.strip(),
            now,
            prospect_id,
        ))

        self.connection.commit()

    # -------------------------------------------------
    # UTILITY
    # -------------------------------------------------

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

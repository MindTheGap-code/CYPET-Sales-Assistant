from datetime import datetime, timedelta
import json


class CampaignEngine:
    """
    CYPET Campaign Engine.

    This is the first campaign layer of the Sales Assistant.
    It does NOT send emails.

    Responsibilities:
    - create campaigns
    - define communication steps
    - enroll prospects
    - schedule the next step
    - stop a campaign member when a reply is detected
    - expose campaign status/history
    """

    STATUS_DRAFT = "DRAFT"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_PAUSED = "PAUSED"
    STATUS_COMPLETED = "COMPLETED"

    MEMBER_ACTIVE = "ACTIVE"
    MEMBER_WAITING = "WAITING_FOR_CUSTOMER"
    MEMBER_REPLIED = "REPLIED"
    MEMBER_COMPLETED = "COMPLETED"
    MEMBER_STOPPED = "STOPPED"

    CHANNEL_EMAIL = "EMAIL"

    def __init__(self, db, automation_engine=None):
        self.db = db
        self.automation = automation_engine
        self._ensure_schema()

    # -------------------------------------------------
    # SCHEMA
    # -------------------------------------------------

    def _ensure_schema(self):
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                channel TEXT DEFAULT 'EMAIL',
                status TEXT DEFAULT 'DRAFT',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                name TEXT NOT NULL,
                delay_days INTEGER DEFAULT 0,
                subject_template TEXT DEFAULT '',
                body_template TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                UNIQUE(campaign_id, step_number),
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
            )
        """)

        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                prospect_id INTEGER NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                current_step INTEGER DEFAULT 1,
                next_action_date TEXT,
                enrolled_at TEXT NOT NULL,
                replied_at TEXT,
                stopped_at TEXT,
                UNIQUE(campaign_id, prospect_id),
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY(prospect_id) REFERENCES prospects(id)
            )
        """)

        # Commitment-aware campaign fields. These ALTER statements are
        # intentionally idempotent so existing CYPET databases are preserved.
        existing_columns = {
            row[1] for row in self.db.cursor.execute(
                "PRAGMA table_info(campaign_members)"
            ).fetchall()
        }
        for column_sql in (
            ("commitment_type", "TEXT DEFAULT ''"),
            ("commitment_date", "TEXT"),
            ("commitment_note", "TEXT DEFAULT ''"),
            ("commitment_source", "TEXT DEFAULT ''"),
        ):
            column_name, column_def = column_sql
            if column_name not in existing_columns:
                self.db.cursor.execute(
                    f"ALTER TABLE campaign_members ADD COLUMN {column_name} {column_def}"
                )

        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                prospect_id INTEGER,
                member_id INTEGER,
                event_type TEXT NOT NULL,
                step_number INTEGER,
                event_date TEXT NOT NULL,
                details TEXT DEFAULT ''
            )
        """)

        self.db.connection.commit()

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------

    @staticmethod
    def _now():
        return datetime.now().astimezone().isoformat()

    def _campaign(self, campaign_id):
        return self.db.cursor.execute("""
            SELECT *
            FROM campaigns
            WHERE id = ?
            LIMIT 1
        """, (campaign_id,)).fetchone()

    def _member(self, campaign_id, prospect_id):
        return self.db.cursor.execute("""
            SELECT *
            FROM campaign_members
            WHERE campaign_id = ?
              AND prospect_id = ?
            LIMIT 1
        """, (campaign_id, prospect_id)).fetchone()

    def _record_event(
        self,
        campaign_id,
        event_type,
        prospect_id=None,
        member_id=None,
        step_number=None,
        details="",
    ):
        self.db.cursor.execute("""
            INSERT INTO campaign_events (
                campaign_id,
                prospect_id,
                member_id,
                event_type,
                step_number,
                event_date,
                details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_id,
            prospect_id,
            member_id,
            event_type,
            step_number,
            self._now(),
            details or "",
        ))

        self.db.connection.commit()

    # -------------------------------------------------
    # CAMPAIGNS
    # -------------------------------------------------

    def create_campaign(
        self,
        name,
        description="",
        channel=CHANNEL_EMAIL,
    ):
        now = self._now()

        self.db.cursor.execute("""
            INSERT INTO campaigns (
                name,
                description,
                channel,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name.strip(),
            description.strip(),
            channel,
            self.STATUS_DRAFT,
            now,
            now,
        ))

        campaign_id = self.db.cursor.lastrowid
        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "CAMPAIGN_CREATED",
            details=name.strip(),
        )

        return self._campaign(campaign_id)

    def activate_campaign(self, campaign_id):
        campaign = self._campaign(campaign_id)

        if not campaign:
            return None

        step = self.db.cursor.execute("""
            SELECT *
            FROM campaign_steps
            WHERE campaign_id = ?
              AND active = 1
            ORDER BY step_number
            LIMIT 1
        """, (campaign_id,)).fetchone()

        if not step:
            raise ValueError(
                "Cannot activate a campaign without an active step."
            )

        now = self._now()

        self.db.cursor.execute("""
            UPDATE campaigns
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (
            self.STATUS_ACTIVE,
            now,
            campaign_id,
        ))

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "CAMPAIGN_ACTIVATED",
            details="Campaign activated.",
        )

        return self._campaign(campaign_id)

    def pause_campaign(self, campaign_id):
        now = self._now()

        self.db.cursor.execute("""
            UPDATE campaigns
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (
            self.STATUS_PAUSED,
            now,
            campaign_id,
        ))

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "CAMPAIGN_PAUSED",
            details="Campaign paused.",
        )

        return self._campaign(campaign_id)

    # -------------------------------------------------
    # STEPS
    # -------------------------------------------------

    def add_step(
        self,
        campaign_id,
        name,
        delay_days,
        subject_template="",
        body_template="",
        step_number=None,
    ):
        campaign = self._campaign(campaign_id)

        if not campaign:
            raise ValueError("Campaign not found.")

        if step_number is None:
            row = self.db.cursor.execute("""
                SELECT COALESCE(MAX(step_number), 0) + 1
                FROM campaign_steps
                WHERE campaign_id = ?
            """, (campaign_id,)).fetchone()
            step_number = row[0]

        self.db.cursor.execute("""
            INSERT INTO campaign_steps (
                campaign_id,
                step_number,
                name,
                delay_days,
                subject_template,
                body_template,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            campaign_id,
            step_number,
            name.strip(),
            max(0, int(delay_days)),
            subject_template or "",
            body_template or "",
        ))

        step_id = self.db.cursor.lastrowid

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "STEP_CREATED",
            step_number=step_number,
            details=name.strip(),
        )

        return self.db.cursor.execute("""
            SELECT *
            FROM campaign_steps
            WHERE id = ?
        """, (step_id,)).fetchone()

    def get_steps(self, campaign_id):
        return self.db.cursor.execute("""
            SELECT *
            FROM campaign_steps
            WHERE campaign_id = ?
            ORDER BY step_number
        """, (campaign_id,)).fetchall()

    # -------------------------------------------------
    # PROSPECT ENROLLMENT
    # -------------------------------------------------

    def enroll_prospects(self, campaign_id, prospect_ids):
        campaign = self._campaign(campaign_id)

        if not campaign:
            raise ValueError("Campaign not found.")

        first_step = self.db.cursor.execute("""
            SELECT *
            FROM campaign_steps
            WHERE campaign_id = ?
              AND active = 1
            ORDER BY step_number
            LIMIT 1
        """, (campaign_id,)).fetchone()

        if not first_step:
            raise ValueError(
                "Add at least one active campaign step first."
            )

        enrolled = 0
        now = datetime.now().astimezone()

        for prospect_id in prospect_ids:
            prospect = self.db.cursor.execute("""
                SELECT *
                FROM prospects
                WHERE id = ?
                LIMIT 1
            """, (prospect_id,)).fetchone()

            if not prospect:
                continue

            try:
                next_date = (
                    now + timedelta(days=first_step["delay_days"])
                ).date().isoformat()

                self.db.cursor.execute("""
                    INSERT INTO campaign_members (
                        campaign_id,
                        prospect_id,
                        status,
                        current_step,
                        next_action_date,
                        enrolled_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    campaign_id,
                    prospect_id,
                    self.MEMBER_ACTIVE,
                    first_step["step_number"],
                    next_date,
                    now.isoformat(),
                ))

                member_id = self.db.cursor.lastrowid
                enrolled += 1

                self._record_event(
                    campaign_id,
                    "PROSPECT_ENROLLED",
                    prospect_id=prospect_id,
                    member_id=member_id,
                    step_number=first_step["step_number"],
                    details=prospect["domain"],
                )

            except Exception:
                # UNIQUE(campaign_id, prospect_id) protects against
                # accidental double enrollment.
                self.db.connection.rollback()

        self.db.connection.commit()
        return enrolled

    # -------------------------------------------------
    # CUSTOMER COMMITMENTS
    # -------------------------------------------------

    @staticmethod
    def _mid_month_date(year, month):
        return f"{year:04d}-{month:02d}-15"

    def set_customer_commitment(
        self,
        campaign_id,
        prospect_id,
        commitment_type,
        commitment_date,
        note="",
        source="conversation_intelligence",
    ):
        """
        Store a customer-requested follow-up commitment.

        The campaign member is moved to WAITING_FOR_CUSTOMER and any existing
        OPEN CAMPAIGN_STEP_DUE action for the same member/current step is
        rescheduled to the commitment date.
        """
        member = self._member(campaign_id, prospect_id)
        if not member:
            return False

        self.db.cursor.execute(
            """
            UPDATE campaign_members
            SET
                status = ?,
                next_action_date = ?,
                commitment_type = ?,
                commitment_date = ?,
                commitment_note = ?,
                commitment_source = ?
            WHERE id = ?
            """,
            (
                self.MEMBER_WAITING,
                commitment_date,
                commitment_type or "",
                commitment_date,
                note or "",
                source or "",
                member["id"],
            ),
        )

        existing_action = self.db.cursor.execute(
            """
            SELECT id, due_date, title, description
            FROM automation_actions
            WHERE action_type = 'CAMPAIGN_STEP_DUE'
              AND status = 'OPEN'
              AND campaign_id = ?
              AND campaign_member_id = ?
              AND campaign_step_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (campaign_id, member["id"], member["current_step"]),
        ).fetchone()

        if existing_action:
            old_due = existing_action["due_date"] or ""
            old_description = existing_action["description"] or ""
            commitment_line = (
                f"Customer requested follow-up on {commitment_date}."
            )

            if commitment_line not in old_description:
                new_description = (
                    old_description.rstrip()
                    + "\\n"
                    + commitment_line
                    + (
                        f" Previous campaign due date: {old_due}."
                        if old_due and old_due != commitment_date
                        else ""
                    )
                )
            else:
                new_description = old_description

            self.db.cursor.execute(
                """
                UPDATE automation_actions
                SET
                    due_date = ?,
                    description = ?
                WHERE id = ?
                  AND status = 'OPEN'
                """,
                (
                    commitment_date,
                    new_description,
                    existing_action["id"],
                ),
            )

            action_detail = (
                f"Existing campaign action {existing_action['id']} "
                f"rescheduled from {old_due or 'unscheduled'} "
                f"to {commitment_date}."
            )
        else:
            action_detail = (
                "No existing open campaign action was available to reschedule."
            )

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "CUSTOMER_COMMITMENT_SET",
            prospect_id=prospect_id,
            member_id=member["id"],
            step_number=member["current_step"],
            details=(
                f"{commitment_type or 'FOLLOW_UP'} | "
                f"date={commitment_date} | "
                f"{note or ''} | "
                f"{action_detail}"
            ).strip(),
        )

        return True
    def get_waiting_commitments(self, on_date=None):
        if on_date is None:
            on_date = datetime.now().astimezone().date().isoformat()

        return self.db.cursor.execute("""
            SELECT
                m.*,
                c.name AS campaign_name,
                p.domain,
                p.company_name
            FROM campaign_members m
            JOIN campaigns c ON c.id = m.campaign_id
            JOIN prospects p ON p.id = m.prospect_id
            WHERE c.status = ?
              AND m.status = ?
              AND m.commitment_date IS NOT NULL
              AND m.commitment_date <= ?
            ORDER BY m.commitment_date ASC, m.id ASC
        """, (
            self.STATUS_ACTIVE,
            self.MEMBER_WAITING,
            on_date,
        )).fetchall()

    def release_due_commitments(self, on_date=None):
        """
        Release customer commitments whose requested follow-up date has
        arrived. The member becomes ACTIVE and keeps the current campaign
        step, so the normal execution engine can create the action.
        """
        if on_date is None:
            on_date = datetime.now().astimezone().date().isoformat()

        rows = self.get_waiting_commitments(on_date)
        released = 0
        for member in rows:
            self.db.cursor.execute("""
                UPDATE campaign_members
                SET
                    status = ?,
                    next_action_date = ?,
                    commitment_note = commitment_note
                WHERE id = ?
                  AND status = ?
            """, (
                self.MEMBER_ACTIVE,
                on_date,
                member["id"],
                self.MEMBER_WAITING,
            ))
            if self.db.cursor.rowcount:
                released += 1
                self._record_event(
                    member["campaign_id"],
                    "CUSTOMER_COMMITMENT_DUE",
                    prospect_id=member["prospect_id"],
                    member_id=member["id"],
                    step_number=member["current_step"],
                    details=(
                        f"Customer requested follow-up on {member['commitment_date']}."
                    ),
                )

        self.db.connection.commit()
        return released

    # -------------------------------------------------
    # CAMPAIGN CONTROL
    # -------------------------------------------------

    def stop_member(self, campaign_id, prospect_id, reason=""):
        member = self._member(campaign_id, prospect_id)

        if not member:
            return False

        now = self._now()

        self.db.cursor.execute("""
            UPDATE campaign_members
            SET
                status = ?,
                stopped_at = ?
            WHERE id = ?
        """, (
            self.MEMBER_STOPPED,
            now,
            member["id"],
        ))

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "MEMBER_STOPPED",
            prospect_id=prospect_id,
            member_id=member["id"],
            step_number=member["current_step"],
            details=reason or "Stopped manually.",
        )

        return True

    def mark_reply_received(
        self,
        campaign_id,
        prospect_id,
        details="Customer replied.",
    ):
        member = self._member(campaign_id, prospect_id)

        if not member:
            return False

        now = self._now()

        self.db.cursor.execute("""
            UPDATE campaign_members
            SET
                status = ?,
                replied_at = ?,
                stopped_at = ?
            WHERE id = ?
        """, (
            self.MEMBER_REPLIED,
            now,
            now,
            member["id"],
        ))

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "REPLY_RECEIVED",
            prospect_id=prospect_id,
            member_id=member["id"],
            step_number=member["current_step"],
            details=details,
        )

        return True

    # -------------------------------------------------
    # DUE COMMUNICATIONS
    # -------------------------------------------------

    def get_due_members(self, campaign_id=None, on_date=None):
        if on_date is None:
            on_date = datetime.now().astimezone().date().isoformat()

        params = [self.STATUS_ACTIVE, self.MEMBER_ACTIVE, self.MEMBER_WAITING, on_date]

        query = """
            SELECT
                m.*,
                c.name AS campaign_name,
                c.channel,
                s.name AS step_name,
                s.subject_template,
                s.body_template,
                s.step_number,
                p.domain,
                p.company_name,
                p.industry,
                p.status AS prospect_status
            FROM campaign_members m
            JOIN campaigns c
              ON c.id = m.campaign_id
            JOIN campaign_steps s
              ON s.campaign_id = m.campaign_id
             AND s.step_number = m.current_step
            JOIN prospects p
              ON p.id = m.prospect_id
            WHERE c.status = ?
              AND m.status IN (?, ?)
              AND m.next_action_date <= ?
        """

        if campaign_id is not None:
            query += " AND m.campaign_id = ?"
            params.append(campaign_id)

        query += """
            ORDER BY m.next_action_date ASC, m.id ASC
        """

        return self.db.cursor.execute(query, params).fetchall()

    # -------------------------------------------------
    # STEP PROGRESSION
    # -------------------------------------------------

    def advance_member(self, campaign_id, prospect_id):
        member = self._member(campaign_id, prospect_id)

        if not member:
            return None

        next_step = self.db.cursor.execute("""
            SELECT *
            FROM campaign_steps
            WHERE campaign_id = ?
              AND step_number > ?
              AND active = 1
            ORDER BY step_number
            LIMIT 1
        """, (
            campaign_id,
            member["current_step"],
        )).fetchone()

        if not next_step:
            now = self._now()

            self.db.cursor.execute("""
                UPDATE campaign_members
                SET
                    status = ?,
                    next_action_date = NULL
                WHERE id = ?
            """, (
                self.MEMBER_COMPLETED,
                member["id"],
            ))

            self.db.connection.commit()

            self._record_event(
                campaign_id,
                "MEMBER_COMPLETED",
                prospect_id=prospect_id,
                member_id=member["id"],
                step_number=member["current_step"],
                details="Campaign sequence completed.",
            )

            return None

        next_date = (
            datetime.now().astimezone()
            + timedelta(days=next_step["delay_days"])
        ).date().isoformat()

        self.db.cursor.execute("""
            UPDATE campaign_members
            SET
                current_step = ?,
                next_action_date = ?
            WHERE id = ?
        """, (
            next_step["step_number"],
            next_date,
            member["id"],
        ))

        self.db.connection.commit()

        self._record_event(
            campaign_id,
            "STEP_SCHEDULED",
            prospect_id=prospect_id,
            member_id=member["id"],
            step_number=next_step["step_number"],
            details=next_step["name"],
        )

        return next_step

    # -------------------------------------------------
    # STATUS / DASHBOARD
    # -------------------------------------------------

    def get_campaigns(self):
        return self.db.cursor.execute("""
            SELECT
                c.*,
                COUNT(m.id) AS members,
                SUM(
                    CASE WHEN m.status = 'ACTIVE'
                    THEN 1 ELSE 0 END
                ) AS active_members,
                SUM(
                    CASE WHEN m.status = 'REPLIED'
                    THEN 1 ELSE 0 END
                ) AS replies,
                SUM(
                    CASE WHEN m.status = 'COMPLETED'
                    THEN 1 ELSE 0 END
                ) AS completed_members
            FROM campaigns c
            LEFT JOIN campaign_members m
              ON m.campaign_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """).fetchall()

    def get_campaign_history(self, campaign_id, limit=100):
        return self.db.cursor.execute("""
            SELECT *
            FROM campaign_events
            WHERE campaign_id = ?
            ORDER BY event_date DESC, id DESC
            LIMIT ?
        """, (campaign_id, limit)).fetchall()

    def campaign_summary(self, campaign_id):
        campaign = self._campaign(campaign_id)

        if not campaign:
            return None

        row = self.db.cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN status = 'REPLIED' THEN 1 ELSE 0 END) AS replied,
                SUM(CASE WHEN status = 'STOPPED' THEN 1 ELSE 0 END) AS stopped,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed
            FROM campaign_members
            WHERE campaign_id = ?
        """, (campaign_id,)).fetchone()

        return {
            "campaign": campaign,
            "total": row["total"] or 0,
            "active": row["active"] or 0,
            "replied": row["replied"] or 0,
            "stopped": row["stopped"] or 0,
            "completed": row["completed"] or 0,
        }

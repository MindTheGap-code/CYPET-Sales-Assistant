from datetime import date, datetime, timedelta

from config import EXCLUDED_DOMAINS
from modules.database import Database
from modules.outlook_inbox import OutlookInboxReader


class AutomationEngine:
    """
    CYPET Sales Assistant - Automation Engine v5.

    Rules:
    - Follow-up overdue / today / scheduled
    - New prospect qualification
    - Qualified prospect reactivation
    - Confirmed Outlook replies -> REVIEW_REPLY
    - Automation event history

    The engine creates suggested actions only.
    It does not send emails or change prospect status automatically.
    """

    ACTION_FOLLOWUP_OVERDUE = "FOLLOW_UP_OVERDUE"
    ACTION_FOLLOWUP_TODAY = "FOLLOW_UP_TODAY"
    ACTION_FOLLOWUP_SCHEDULED = "FOLLOW_UP_SCHEDULED"
    ACTION_QUALIFY_PROSPECT = "QUALIFY_PROSPECT"
    ACTION_REACTIVATE_PROSPECT = "REACTIVATE_PROSPECT"
    ACTION_REVIEW_REPLY = "REVIEW_REPLY"

    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_NORMAL = "NORMAL"

    def __init__(self, database=None):
        self.db = database or Database()
        self.inbox = OutlookInboxReader()

        self._create_actions_table()
        self._migrate_actions_table()
        self._create_events_table()
        self._backfill_reply_contacts()

    # -------------------------------------------------
    # ACTION TABLE
    # -------------------------------------------------

    def _create_actions_table(self):
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER,
                domain TEXT DEFAULT '',
                action_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                status TEXT DEFAULT 'OPEN',
                source TEXT DEFAULT 'AUTOMATION',
                created_at TEXT NOT NULL,
                completed_at TEXT DEFAULT '',
                conversation_id TEXT DEFAULT '',
                source_entry_id TEXT DEFAULT '',
                received_at TEXT DEFAULT '',
                contact_name TEXT DEFAULT '',
                contact_email TEXT DEFAULT '',
                UNIQUE(prospect_id, action_type, due_date)
            )
        """)
        self.db.connection.commit()

    def _migrate_actions_table(self):
        columns = {
            row["name"]
            for row in self.db.cursor.execute(
                "PRAGMA table_info(automation_actions)"
            ).fetchall()
        }

        additions = {
            "conversation_id": "TEXT DEFAULT ''",
            "source_entry_id": "TEXT DEFAULT ''",
            "received_at": "TEXT DEFAULT ''",
            "contact_name": "TEXT DEFAULT ''",
            "contact_email": "TEXT DEFAULT ''",
            "campaign_id": "INTEGER",
            "campaign_member_id": "INTEGER",
            "campaign_step_id": "INTEGER",
        }

        for name, definition in additions.items():
            if name not in columns:
                self.db.cursor.execute(
                    f"ALTER TABLE automation_actions ADD COLUMN {name} {definition}"
                )

        self.db.connection.commit()

    # -------------------------------------------------
    # EVENT HISTORY
    # -------------------------------------------------

    def _create_events_table(self):
        """
        Persistent history of automation events.

        This table is deliberately independent from automation_actions:
        an Action can be completed/dismissed while the underlying event
        remains part of the commercial history.
        """
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                prospect_id INTEGER,
                domain TEXT DEFAULT '',
                action_id INTEGER,
                conversation_id TEXT DEFAULT '',
                source_entry_id TEXT DEFAULT '',
                contact_name TEXT DEFAULT '',
                contact_email TEXT DEFAULT '',
                subject TEXT DEFAULT '',
                event_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                details TEXT DEFAULT ''
            )
        """)
        self.db.connection.commit()

    def _record_event(
        self,
        event_key,
        event_type,
        prospect_id=None,
        domain="",
        action_id=None,
        conversation_id="",
        source_entry_id="",
        contact_name="",
        contact_email="",
        subject="",
        event_date="",
        details="",
    ):
        now = datetime.now().astimezone().isoformat()

        self.db.cursor.execute("""
            INSERT OR IGNORE INTO automation_events (
                event_key,
                event_type,
                prospect_id,
                domain,
                action_id,
                conversation_id,
                source_entry_id,
                contact_name,
                contact_email,
                subject,
                event_date,
                created_at,
                details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_key,
            event_type,
            prospect_id,
            domain or "",
            action_id,
            conversation_id or "",
            source_entry_id or "",
            contact_name or "",
            contact_email or "",
            subject or "",
            event_date or now,
            now,
            details or "",
        ))

        self.db.connection.commit()

        return self.db.cursor.rowcount > 0

    def get_recent_events(self, limit=50):
        self.db.cursor.execute("""
            SELECT
                e.*,
                COALESCE(
                    NULLIF(p.company_name, ''),
                    p.domain,
                    e.domain
                ) AS company_name
            FROM automation_events e
            LEFT JOIN prospects p ON p.id = e.prospect_id
            ORDER BY e.event_date DESC, e.id DESC
            LIMIT ?
        """, (limit,))

        return self.db.cursor.fetchall()

    # -------------------------------------------------
    # BACKFILL
    # -------------------------------------------------

    def _backfill_reply_contacts(self):
        """
        Backfill contact_name/contact_email for existing REVIEW_REPLY
        actions created by earlier engine versions.
        """
        rows = self.db.cursor.execute("""
            SELECT
                id,
                source_entry_id,
                description,
                contact_name,
                contact_email
            FROM automation_actions
            WHERE action_type = 'REVIEW_REPLY'
              AND status = 'OPEN'
        """).fetchall()

        changed = False

        for row in rows:
            contact_name = (row["contact_name"] or "").strip()
            contact_email = (row["contact_email"] or "").strip()

            if row["source_entry_id"]:
                try:
                    mail = self.inbox.namespace.GetItemFromID(
                        row["source_entry_id"]
                    )

                    outlook_name = self._outlook_sender_name(mail)
                    outlook_email = self._normalize_email(
                        self.inbox.sender_smtp(mail)
                    )

                    if outlook_name:
                        contact_name = outlook_name

                    if outlook_email:
                        contact_email = outlook_email

                except Exception:
                    pass

            if not contact_email:
                import re

                description = row["description"] or ""

                match = re.search(
                    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
                    description,
                )

                if match:
                    contact_email = match.group(0).lower()

            if contact_name or contact_email:
                self.db.cursor.execute("""
                    UPDATE automation_actions
                    SET
                        contact_name = ?,
                        contact_email = ?
                    WHERE id = ?
                """, (
                    contact_name,
                    contact_email,
                    row["id"],
                ))

                changed = True

        if changed:
            self.db.connection.commit()

    # -------------------------------------------------
    # MAIN RUN
    # -------------------------------------------------

    def run(self, inbox_limit=100):
        started_at = datetime.now().astimezone().isoformat()

        prospects = self._get_prospects()
        generated = []

        for prospect in prospects:
            generated.extend(
                self._evaluate_prospect(prospect)
            )

        reply_actions = self._detect_replies(inbox_limit)
        generated.extend(reply_actions)

        actions = self.get_open_actions()

        return {
            "started_at": started_at,
            "prospects_checked": len(prospects),
            "actions_generated": len(generated),
            "open_actions": len(actions),
            "reply_actions_generated": len(reply_actions),
            "actions": actions,
        }

    # -------------------------------------------------
    # PROSPECT RULES
    # -------------------------------------------------

    def _get_prospects(self):
        self.db.cursor.execute("""
            SELECT
                p.id,
                p.domain,
                p.company_name,
                p.industry,
                p.status,
                p.notes,
                p.created_at,
                p.updated_at,
                p.next_action_date,
                p.next_action_note,
                COUNT(e.id) AS contacts,
                MAX(e.sent_date) AS last_contact
            FROM prospects p
            LEFT JOIN emails e
                ON e.domain = p.domain
            GROUP BY
                p.id,
                p.domain,
                p.company_name,
                p.industry,
                p.status,
                p.notes,
                p.created_at,
                p.updated_at,
                p.next_action_date,
                p.next_action_note
            ORDER BY p.domain ASC
        """)

        return self.db.cursor.fetchall()

    def _evaluate_prospect(self, prospect):
        actions = []

        status = (prospect["status"] or "").strip()
        next_date = self._parse_date(
            prospect["next_action_date"]
        )
        today = date.today()

        if next_date and next_date < today and status != "Customer":
            action = self._create_action(
                prospect,
                self.ACTION_FOLLOWUP_OVERDUE,
                self.PRIORITY_HIGH,
                f"{self._company(prospect)} - follow-up overdue",
                prospect["next_action_note"]
                or "The scheduled follow-up date has passed.",
                prospect["next_action_date"],
            )

            if action:
                actions.append(action)

        elif (
            next_date
            and next_date == today
            and status != "Customer"
        ):
            action = self._create_action(
                prospect,
                self.ACTION_FOLLOWUP_TODAY,
                self.PRIORITY_HIGH,
                f"{self._company(prospect)} - follow-up today",
                prospect["next_action_note"]
                or "A follow-up is scheduled for today.",
                prospect["next_action_date"],
            )

            if action:
                actions.append(action)

        elif (
            next_date
            and next_date > today
            and status != "Customer"
        ):
            action = self._create_action(
                prospect,
                self.ACTION_FOLLOWUP_SCHEDULED,
                self.PRIORITY_NORMAL,
                f"{self._company(prospect)} - follow-up scheduled",
                prospect["next_action_note"]
                or "A future follow-up is scheduled.",
                prospect["next_action_date"],
            )

            if action:
                actions.append(action)

        if status == "New" and int(
            prospect["contacts"] or 0
        ) == 0:
            action = self._create_action(
                prospect,
                self.ACTION_QUALIFY_PROSPECT,
                self.PRIORITY_NORMAL,
                f"{self._company(prospect)} - qualify prospect",
                "This prospect is new and has no email activity recorded.",
                "",
            )

            if action:
                actions.append(action)

        last_contact = self._parse_datetime(
            prospect["last_contact"]
        )

        if (
            status == "Qualified"
            and last_contact
            and (
                datetime.now().astimezone() - last_contact
            ).days > 30
        ):
            action = self._create_action(
                prospect,
                self.ACTION_REACTIVATE_PROSPECT,
                self.PRIORITY_HIGH,
                f"{self._company(prospect)} - reactivate prospect",
                "The prospect is qualified but has had no recorded email activity for more than 30 days.",
                "",
            )

            if action:
                actions.append(action)

        return actions

    # -------------------------------------------------
    # OUTLOOK REPLIES
    # -------------------------------------------------

    def _detect_replies(self, inbox_limit):
        sent_rows = self.db.cursor.execute("""
            SELECT
                outlook_id,
                recipient_name,
                recipient_email,
                subject,
                sent_date,
                domain
            FROM emails
            WHERE recipient_email <> ''
            ORDER BY sent_date ASC
        """).fetchall()

        sent_by_key = {}

        for row in sent_rows:
            email = self._normalize_email(
                row["recipient_email"]
            )
            subject = self.inbox.normalize_subject(
                row["subject"]
            )

            if not email or not subject:
                continue

            sent_by_key.setdefault(
                (email, subject),
                []
            ).append(row)

        messages = self.inbox.get_last_messages(
            inbox_limit
        )

        confirmed = []

        for mail in messages:
            try:
                sender = self._normalize_email(
                    self.inbox.sender_smtp(mail)
                )
                subject = self.inbox.normalize_subject(
                    mail.Subject
                )

                if not sender or not subject:
                    continue

                sender_domain = (
                    sender.split("@", 1)[1]
                    if "@" in sender
                    else ""
                )

                if sender_domain in EXCLUDED_DOMAINS:
                    continue

                candidates = sent_by_key.get(
                    (sender, subject),
                    []
                )

                if not candidates:
                    continue

                received = self._parse_datetime(
                    mail.ReceivedTime
                )
                conversation_id = self._conversation_id(
                    mail
                )

                if not received or not conversation_id:
                    continue

                previous = []

                for row in candidates:
                    sent = self._parse_datetime(
                        row["sent_date"]
                    )

                    if not sent or sent >= received:
                        continue

                    try:
                        original = (
                            self.inbox.namespace.GetItemFromID(
                                row["outlook_id"]
                            )
                        )

                        original_conversation = (
                            self._conversation_id(original)
                        )

                    except Exception:
                        original_conversation = ""

                    if (
                        original_conversation
                        and original_conversation
                        == conversation_id
                    ):
                        previous.append(
                            (sent, row)
                        )

                if not previous:
                    continue

                previous.sort(
                    key=lambda item: item[0],
                    reverse=True
                )

                sent_time, sent_row = previous[0]

                sender_name = (
                    self._outlook_sender_name(mail)
                )

                contact_name = (
                    sender_name
                    or sent_row["recipient_name"]
                    or sender
                )

                confirmed.append({
                    "sender": sender,
                    "sender_name": contact_name,
                    "domain": (
                        sent_row["domain"]
                        or sender_domain
                    ),
                    "subject": (
                        mail.Subject
                        or "(No subject)"
                    ),
                    "received": received,
                    "matched_sent": sent_time,
                    "conversation_id": conversation_id,
                    "entry_id": self._entry_id(mail),
                })

            except Exception:
                continue

        # One actionable item per sender + conversation:
        # always keep the latest reply.
        latest = {}

        for item in confirmed:
            key = (
                item["sender"],
                item["conversation_id"],
            )

            existing = latest.get(key)

            if (
                existing is None
                or item["received"]
                > existing["received"]
            ):
                latest[key] = item

        actions = []

        for item in latest.values():
            prospect = self._prospect_by_domain(
                item["domain"]
            )

            if prospect is None:
                continue

            action = self._create_reply_action(
                prospect,
                item
            )

            if action:
                actions.append(action)

        return actions

    def _create_reply_action(self, prospect, reply):
        now = datetime.now().astimezone().isoformat()

        # If the exact reply is already represented by an action,
        # never create it again.
        existing_reply = self.db.cursor.execute("""
            SELECT id, status
            FROM automation_actions
            WHERE action_type = ?
              AND source_entry_id = ?
            LIMIT 1
        """, (
            self.ACTION_REVIEW_REPLY,
            reply["entry_id"],
        )).fetchone()

        if existing_reply:
            return None

        # If there is already an open action for this conversation,
        # update it to the latest reply instead of creating a duplicate.
        open_action = self.db.cursor.execute("""
            SELECT id
            FROM automation_actions
            WHERE action_type = ?
              AND conversation_id = ?
              AND status = 'OPEN'
            ORDER BY id DESC
            LIMIT 1
        """, (
            self.ACTION_REVIEW_REPLY,
            reply["conversation_id"],
        )).fetchone()

        display_name = self._company(prospect)

        description = (
            f"{reply['sender_name']} replied. "
            f"Subject: {reply['subject']}"
        )

        if open_action:
            self.db.cursor.execute("""
                UPDATE automation_actions
                SET
                    domain = ?,
                    title = ?,
                    description = ?,
                    source_entry_id = ?,
                    received_at = ?,
                    contact_name = ?,
                    contact_email = ?
                WHERE id = ?
            """, (
                prospect["domain"],
                f"{display_name} - customer replied",
                description,
                reply["entry_id"],
                reply["received"].isoformat(),
                reply["sender_name"],
                reply["sender"],
                open_action["id"],
            ))

            self.db.connection.commit()

            self._record_event(
                event_key=f"REPLY:{reply['entry_id']}",
                event_type="CUSTOMER_REPLY",
                prospect_id=prospect["id"],
                domain=prospect["domain"],
                action_id=open_action["id"],
                conversation_id=reply["conversation_id"],
                source_entry_id=reply["entry_id"],
                contact_name=reply["sender_name"],
                contact_email=reply["sender"],
                subject=reply["subject"],
                event_date=reply["received"].isoformat(),
                details="Existing open REVIEW_REPLY action updated to latest reply.",
            )

            return self.db.cursor.execute("""
                SELECT *
                FROM automation_actions
                WHERE id = ?
            """, (open_action["id"],)).fetchone()

        self.db.cursor.execute("""
            INSERT INTO automation_actions (
                prospect_id,
                domain,
                action_type,
                priority,
                title,
                description,
                due_date,
                status,
                source,
                created_at,
                conversation_id,
                source_entry_id,
                received_at,
                contact_name,
                contact_email
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, '',
                'OPEN', 'OUTLOOK', ?,
                ?, ?, ?, ?, ?
            )
        """, (
            prospect["id"],
            prospect["domain"],
            self.ACTION_REVIEW_REPLY,
            self.PRIORITY_HIGH,
            f"{display_name} - customer replied",
            description,
            now,
            reply["conversation_id"],
            reply["entry_id"],
            reply["received"].isoformat(),
            reply["sender_name"],
            reply["sender"],
        ))

        self.db.connection.commit()

        action = self.db.cursor.execute("""
            SELECT *
            FROM automation_actions
            WHERE id = last_insert_rowid()
        """).fetchone()

        self._record_event(
            event_key=f"REPLY:{reply['entry_id']}",
            event_type="CUSTOMER_REPLY",
            prospect_id=prospect["id"],
            domain=prospect["domain"],
            action_id=action["id"],
            conversation_id=reply["conversation_id"],
            source_entry_id=reply["entry_id"],
            contact_name=reply["sender_name"],
            contact_email=reply["sender"],
            subject=reply["subject"],
            event_date=reply["received"].isoformat(),
            details="New actionable customer reply detected.",
        )

        return action

    # -------------------------------------------------
    # ACTION STORAGE
    # -------------------------------------------------

    def _create_action(
        self,
        prospect,
        action_type,
        priority,
        title,
        description,
        due_date,
    ):
        now = datetime.now().astimezone().isoformat()

        self.db.cursor.execute("""
            INSERT OR IGNORE INTO automation_actions (
                prospect_id,
                domain,
                action_type,
                priority,
                title,
                description,
                due_date,
                status,
                source,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                'OPEN', 'AUTOMATION', ?
            )
        """, (
            prospect["id"],
            prospect["domain"],
            action_type,
            priority,
            title,
            description,
            due_date or "",
            now,
        ))

        self.db.connection.commit()

        if self.db.cursor.rowcount == 0:
            return None

        action = self.db.cursor.execute("""
            SELECT *
            FROM automation_actions
            WHERE id = last_insert_rowid()
        """).fetchone()

        self._record_event(
            event_key=f"ACTION:{action['id']}",
            event_type="ACTION_CREATED",
            prospect_id=prospect["id"],
            domain=prospect["domain"],
            action_id=action["id"],
            event_date=now,
            details=(
                f"{action_type}: {title}"
            ),
        )

        return action

    def get_open_actions(self):
        self.db.cursor.execute("""
            SELECT
                a.*,
                COALESCE(
                    NULLIF(p.company_name, ''),
                    p.domain,
                    a.domain
                ) AS company_name
            FROM automation_actions a
            LEFT JOIN prospects p
                ON p.id = a.prospect_id
            WHERE a.status = 'OPEN'
            ORDER BY
                CASE a.priority
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    ELSE 3
                END,
                CASE
                    WHEN a.due_date = '' THEN 1
                    ELSE 0
                END,
                a.due_date ASC,
                a.created_at DESC
        """)

        return self.db.cursor.fetchall()

    def complete_action(self, action_id):
        now = datetime.now().astimezone().isoformat()

        self.db.cursor.execute("""
            UPDATE automation_actions
            SET
                status = 'COMPLETED',
                completed_at = ?
            WHERE id = ?
              AND status = 'OPEN'
        """, (
            now,
            action_id,
        ))

        self.db.connection.commit()

        return self.db.cursor.rowcount > 0

    def complete_action_with_next_step(self, action_id):
        """
        Complete an action and, when appropriate, create the next
        commercial step automatically.

        Current workflow:
        REVIEW_REPLY -> FOLLOW_UP_SCHEDULED (+5 days)

        Other action types are simply completed. This avoids creating
        endless automatic follow-ups while still making the reply
        workflow continuous.
        """
        now = datetime.now().astimezone().isoformat()

        action = self.db.cursor.execute("""
            SELECT *
            FROM automation_actions
            WHERE id = ?
              AND status = 'OPEN'
            LIMIT 1
        """, (action_id,)).fetchone()

        if not action:
            return {
                "completed": False,
                "next_action": None,
            }

        self.db.cursor.execute("""
            UPDATE automation_actions
            SET
                status = 'COMPLETED',
                completed_at = ?
            WHERE id = ?
              AND status = 'OPEN'
        """, (now, action_id))

        self.db.connection.commit()

        if self.db.cursor.rowcount == 0:
            return {
                "completed": False,
                "next_action": None,
            }

        self._record_event(
            event_key=f"COMPLETED:{action_id}:{now}",
            event_type="ACTION_COMPLETED",
            prospect_id=action["prospect_id"],
            domain=action["domain"],
            action_id=action_id,
            conversation_id=action["conversation_id"],
            source_entry_id=action["source_entry_id"],
            contact_name=action["contact_name"],
            contact_email=action["contact_email"],
            subject="",
            event_date=now,
            details=f"Completed action: {action['action_type']}",
        )

        next_action = None

        if action["action_type"] == "CAMPAIGN_STEP_DUE":
            # Campaign actions are completed through the same Actions UI,
            # but their progression belongs to CampaignEngine.
            # Completing the action advances the campaign member to the
            # next scheduled step. No email is sent here.
            campaign_id = action["campaign_id"]

            if campaign_id:
                from modules.campaign_engine import CampaignEngine

                campaign_engine = CampaignEngine(self.db)

                campaign_engine.advance_member(
                    campaign_id,
                    action["prospect_id"],
                )

            return {
                "completed": True,
                "next_action": None,
            }

        if action["action_type"] == self.ACTION_REVIEW_REPLY:
            due = (
                datetime.now().astimezone()
                + timedelta(days=5)
            ).date().isoformat()

            prospect = self.db.cursor.execute("""
                SELECT *
                FROM prospects
                WHERE id = ?
                LIMIT 1
            """, (action["prospect_id"],)).fetchone()

            if prospect:
                # Use a unique due date for the workflow transition.
                # If the same follow-up already exists, reuse it.
                existing_next = self.db.cursor.execute("""
                    SELECT *
                    FROM automation_actions
                    WHERE prospect_id = ?
                      AND action_type = ?
                      AND due_date = ?
                    LIMIT 1
                """, (
                    prospect["id"],
                    self.ACTION_FOLLOWUP_SCHEDULED,
                    due,
                )).fetchone()

                if existing_next:
                    next_action = existing_next
                else:
                    next_action = self._create_action(
                        prospect,
                        self.ACTION_FOLLOWUP_SCHEDULED,
                        self.PRIORITY_HIGH,
                        f"{self._company(prospect)} - follow-up after reply",
                        (
                            f"Follow up with {action['contact_name'] or action['contact_email'] or 'the contact'} "
                            "after reviewing the customer reply."
                        ),
                        due,
                    )

        return {
            "completed": True,
            "next_action": next_action,
        }

    def dismiss_action(self, action_id):
        self.db.cursor.execute("""
            UPDATE automation_actions
            SET status = 'DISMISSED'
            WHERE id = ?
              AND status = 'OPEN'
        """, (action_id,))

        self.db.connection.commit()

        return self.db.cursor.rowcount > 0

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------

    def _prospect_by_domain(self, domain):
        if not domain:
            return None

        return self.db.cursor.execute("""
            SELECT *
            FROM prospects
            WHERE LOWER(domain) = LOWER(?)
            LIMIT 1
        """, (domain,)).fetchone()

    @staticmethod
    def _company(prospect):
        return (
            prospect["company_name"]
            or prospect["domain"]
            or "Unknown prospect"
        )

    @staticmethod
    def _normalize_email(value):
        return (value or "").strip().lower()

    @staticmethod
    def _conversation_id(mail):
        try:
            return str(
                mail.ConversationID or ""
            ).strip()
        except Exception:
            return ""

    @staticmethod
    def _entry_id(mail):
        try:
            return str(
                mail.EntryID or ""
            ).strip()
        except Exception:
            return ""

    @staticmethod
    def _outlook_sender_name(mail):
        try:
            return str(
                mail.SenderName or ""
            ).strip()
        except Exception:
            return ""

    @staticmethod
    def _parse_date(value):
        if not value:
            return None

        try:
            return datetime.strptime(
                str(value),
                "%Y-%m-%d"
            ).date()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )

            return (
                parsed.astimezone()
                if parsed.tzinfo is None
                else parsed
            )

        except (TypeError, ValueError):
            return None

from datetime import datetime

from modules.database import Database
from modules.campaign_engine import CampaignEngine


class CampaignExecutionEngine:
    """
    CYPET Sales Assistant - Campaign Execution Engine.

    This layer does NOT send emails.

    Responsibilities:
    - inspect ACTIVE campaigns
    - find campaign members whose current step is due
    - create a controlled automation action for each due communication
    - keep the campaign member on the same step until the action is
      explicitly completed
    - advance the campaign sequence only after completion
    """

    ACTION_CAMPAIGN_STEP_DUE = "CAMPAIGN_STEP_DUE"

    PRIORITY_HIGH = "HIGH"

    SOURCE_CAMPAIGN = "CAMPAIGN"

    def __init__(self, database=None):
        self.db = database or Database()
        self.campaigns = CampaignEngine(self.db)
        self._ensure_action_columns()

    # ---------------------------------------------------------
    # SCHEMA
    # ---------------------------------------------------------

    def _ensure_action_columns(self):
        """
        Add campaign-specific references to automation_actions.

        Existing installations are migrated in place. No existing
        automation actions are deleted or modified.
        """
        columns = {
            row["name"]
            for row in self.db.cursor.execute(
                "PRAGMA table_info(automation_actions)"
            ).fetchall()
        }

        additions = {
            "campaign_id": "INTEGER",
            "campaign_member_id": "INTEGER",
            "campaign_step_id": "INTEGER",
        }

        changed = False

        for name, definition in additions.items():
            if name not in columns:
                self.db.cursor.execute(
                    f"ALTER TABLE automation_actions ADD COLUMN {name} {definition}"
                )
                changed = True

        if changed:
            self.db.connection.commit()

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------

    def run(self, campaign_id=None, on_date=None):
        """
        Evaluate due campaign communications.

        Returns generated actions and does not send any email.
        """
        # Release customer-requested waiting commitments whose date has
        # arrived before evaluating normal campaign due members. This keeps
        # the member on its current step while respecting the customer's
        # requested timing.
        released = self.campaigns.release_due_commitments(
            on_date=on_date,
        )

        due_members = self.campaigns.get_due_members(
            campaign_id=campaign_id,
            on_date=on_date,
        )

        generated = []

        for member in due_members:
            action = self._create_due_action(member)

            if action is not None:
                generated.append(action)

        return {
            "checked": len(due_members),
            "released_commitments": released,
            "actions_generated": len(generated),
            "actions": generated,
        }

    # ---------------------------------------------------------
    # ACTION CREATION
    # ---------------------------------------------------------

    def _create_due_action(self, member):
        existing = self.db.cursor.execute(
            """
            SELECT *
            FROM automation_actions
            WHERE action_type = ?
              AND campaign_id = ?
              AND campaign_member_id = ?
              AND campaign_step_id = ?
              AND status = 'OPEN'
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                self.ACTION_CAMPAIGN_STEP_DUE,
                member["campaign_id"],
                member["id"],
                member["step_number"],
            ),
        ).fetchone()

        if existing:
            return None

        company = (
            member["company_name"]
            or member["domain"]
            or "Unknown prospect"
        )

        contact = self._contact_for_prospect(
            member["prospect_id"]
        )

        contact_label = (
            contact["name"]
            or contact["email"]
            or member["domain"]
            or "contact"
        )

        subject = (
            member["subject_template"]
            or member["step_name"]
            or "Campaign communication"
        )

        description = (
            f"Campaign: {member['campaign_name']}\n"
            f"Step {member['step_number']}: {member['step_name']}\n"
            f"Prepare communication for {contact_label}.\n"
            f"Subject: {subject}\n"
            "No email was sent automatically."
        )

        now = datetime.now().astimezone().isoformat()

        self.db.cursor.execute(
            """
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
                campaign_id,
                campaign_member_id,
                campaign_step_id,
                contact_name,
                contact_email
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                'OPEN', ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                member["prospect_id"],
                member["domain"] or "",
                self.ACTION_CAMPAIGN_STEP_DUE,
                self.PRIORITY_HIGH,
                f"{company} - {member['step_name']}",
                description,
                member["next_action_date"] or "",
                self.SOURCE_CAMPAIGN,
                now,
                member["campaign_id"],
                member["id"],
                member["step_number"],
                contact["name"],
                contact["email"],
            ),
        )

        action_id = self.db.cursor.lastrowid

        self.db.connection.commit()

        return self.db.cursor.execute(
            """
            SELECT *
            FROM automation_actions
            WHERE id = ?
            """,
            (action_id,),
        ).fetchone()

    # ---------------------------------------------------------
    # COMPLETION
    # ---------------------------------------------------------

    def complete_action(self, action_id):
        """
        Complete a campaign action and advance its campaign member.

        This method is intentionally separate from email sending.
        """
        action = self.db.cursor.execute(
            """
            SELECT *
            FROM automation_actions
            WHERE id = ?
              AND action_type = ?
              AND status = 'OPEN'
            LIMIT 1
            """,
            (
                action_id,
                self.ACTION_CAMPAIGN_STEP_DUE,
            ),
        ).fetchone()

        if not action:
            return {
                "completed": False,
                "next_step": None,
            }

        self.db.cursor.execute(
            """
            UPDATE automation_actions
            SET
                status = 'COMPLETED',
                completed_at = ?
            WHERE id = ?
              AND status = 'OPEN'
            """,
            (
                datetime.now().astimezone().isoformat(),
                action_id,
            ),
        )

        self.db.connection.commit()

        if self.db.cursor.rowcount == 0:
            return {
                "completed": False,
                "next_step": None,
            }

        next_step = self.campaigns.advance_member(
            action["campaign_id"],
            action["prospect_id"],
        )

        return {
            "completed": True,
            "next_step": next_step,
        }

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _contact_for_prospect(self, prospect_id):
        """
        Return the best available contact data without assuming a
        particular prospect schema.
        """
        columns = {
            row["name"]
            for row in self.db.cursor.execute(
                "PRAGMA table_info(prospects)"
            ).fetchall()
        }

        name_column = next(
            (
                column
                for column in (
                    "contact_name",
                    "name",
                    "full_name",
                )
                if column in columns
            ),
            None,
        )

        email_column = next(
            (
                column
                for column in (
                    "email",
                    "email_address",
                )
                if column in columns
            ),
            None,
        )

        select_parts = []

        if name_column:
            select_parts.append(
                f'"{name_column}" AS contact_name'
            )

        if email_column:
            select_parts.append(
                f'"{email_column}" AS contact_email'
            )

        if not select_parts:
            return {
                "name": "",
                "email": "",
            }

        row = self.db.cursor.execute(
            f"""
            SELECT {", ".join(select_parts)}
            FROM prospects
            WHERE id = ?
            LIMIT 1
            """,
            (prospect_id,),
        ).fetchone()

        if not row:
            return {
                "name": "",
                "email": "",
            }

        return {
            "name": (row["contact_name"] or "").strip()
            if "contact_name" in row.keys()
            else "",
            "email": (row["contact_email"] or "").strip().lower()
            if "contact_email" in row.keys()
            else "",
        }


if __name__ == "__main__":
    db = Database()
    engine = CampaignExecutionEngine(db)
    result = engine.run()

    print("CAMPAIGN EXECUTION ENGINE")
    print("Due communications checked:", result["checked"])
    print("Actions generated:", result["actions_generated"])

    for action in result["actions"]:
        print(
            f"[{action['priority']}] "
            f"{action['title']} | "
            f"{action['action_type']}"
        )
        print(action["description"])
        print()

    print("No emails sent.")

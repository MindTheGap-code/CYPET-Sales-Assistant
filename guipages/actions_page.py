from datetime import datetime
import re
from PySide6.QtCore import Qt
import win32com.client

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea
)

from modules.database import Database
from modules.outlook_inbox import OutlookInboxReader
from modules.campaign_execution_engine import CampaignExecutionEngine
from modules.conversation_intelligence import ConversationIntelligence


class ActionsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.outlook = OutlookInboxReader()
        self.campaign_execution = CampaignExecutionEngine(self.db)
        self.conversation_intelligence = ConversationIntelligence()

        self.setStyleSheet("""
            QFrame#Header, QFrame#ActionCard {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }
            QLabel#Title {
                color: #1F2937;
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#Subtitle, QLabel#Meta {
                color: #6B7280;
                font-size: 10pt;
            }
            QLabel#Company {
                color: #1F2937;
                font-size: 13pt;
                font-weight: 700;
            }
            QLabel#ActionTitle {
                color: #374151;
                font-size: 11pt;
                font-weight: 600;
            }
            QLabel#PriorityHigh {
                color: #B91C1C;
                background: #FEE2E2;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 9pt;
                font-weight: 700;
            }
            QLabel#PriorityMedium {
                color: #92400E;
                background: #FEF3C7;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 9pt;
                font-weight: 700;
            }
            QLabel#PriorityNormal {
                color: #374151;
                background: #EEF4F8;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 9pt;
                font-weight: 700;
            }
            QPushButton#Primary {
                background: #00A3E0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#Secondary {
                background: #EEF4F8;
                color: #374151;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#Danger {
                background: #FEE2E2;
                color: #991B1B;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel("Actions")
        title.setObjectName("Title")

        subtitle = QLabel("Things that require your attention.")
        subtitle.setObjectName("Subtitle")

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        self.count = QLabel("0 open actions")
        self.count.setObjectName("Subtitle")
        header_layout.addWidget(self.count)

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("Primary")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_button)

        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")

        self.actions_layout = QVBoxLayout(self.container)
        self.actions_layout.setContentsMargins(0, 0, 6, 0)
        self.actions_layout.setSpacing(12)

        scroll.setWidget(self.container)
        root.addWidget(scroll, 1)

        self.refresh()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _priority_label(self, priority):
        label = QLabel(priority or "NORMAL")
        if priority == "HIGH":
            label.setObjectName("PriorityHigh")
        elif priority == "MEDIUM":
            label.setObjectName("PriorityMedium")
        else:
            label.setObjectName("PriorityNormal")
        return label

    def _action_card(self, action):
        card = QFrame()
        card.setObjectName("ActionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(self._priority_label(action["priority"]))

        company = QLabel(
            action["company_name"] or action["domain"] or "Unknown company"
        )
        company.setObjectName("Company")
        top.addWidget(company)
        top.addStretch()

        action_type = QLabel(action["action_type"])
        action_type.setObjectName("Meta")
        top.addWidget(action_type)
        layout.addLayout(top)

        if action["action_type"] == "CAMPAIGN_STEP_DUE":
            campaign_label = QLabel("Campaign communication")
            campaign_label.setObjectName("Meta")
            layout.addWidget(campaign_label)

            contact = " / ".join(
                x for x in (
                    action["contact_name"] or "",
                    action["contact_email"] or "",
                ) if x
            )

            if contact:
                contact_label = QLabel(contact)
                contact_label.setObjectName("Meta")
                contact_label.setWordWrap(True)
                layout.addWidget(contact_label)

        title = QLabel(action["title"])
        title.setObjectName("ActionTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        description = QLabel(action["description"] or "")
        description.setObjectName("Meta")
        description.setWordWrap(True)
        layout.addWidget(description)

        if action["action_type"] == "REVIEW_REPLY":
            contact = " / ".join(
                x for x in (
                    action["contact_name"] or "",
                    action["contact_email"] or ""
                ) if x
            )
            if contact:
                contact_label = QLabel(contact)
                contact_label.setObjectName("Meta")
                contact_label.setWordWrap(True)
                layout.addWidget(contact_label)

        if action["due_date"]:
            due = QLabel(f"Due: {action['due_date']}")
            due.setObjectName("Meta")
            layout.addWidget(due)

        buttons = QHBoxLayout()
        buttons.addStretch()

        if action["action_type"] == "REVIEW_REPLY" and action["source_entry_id"]:
            button = QPushButton("Open Email")
            button.setObjectName("Primary")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False,
                eid=action["source_entry_id"]: self.open_email(eid)
            )
            buttons.addWidget(button)

        if action["action_type"] == "CAMPAIGN_STEP_DUE":
            prepare = QPushButton("Prepare Email")
            prepare.setObjectName("CampaignPrepare")
            prepare.setCursor(Qt.PointingHandCursor)
            prepare.setToolTip(
                "Create an editable email draft in Outlook. Nothing is sent."
            )
            # Explicit styling guarantees a visible blue button even if
            # another stylesheet or inherited state overrides #Primary.
            prepare.setStyleSheet("""
                QPushButton {
                    background-color: #00A3E0;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #008FC4;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #007FAF;
                    color: white;
                }
                QPushButton:disabled {
                    background-color: #B8DCEA;
                    color: white;
                }
            """)
            prepare.clicked.connect(
                lambda checked=False,
                aid=action["id"]: self.prepare_campaign_email(aid)
            )
            buttons.addWidget(prepare)

        done = QPushButton("Done")
        done.setObjectName("Secondary")
        done.setCursor(Qt.PointingHandCursor)
        done.clicked.connect(
            lambda checked=False,
            aid=action["id"],
            atype=action["action_type"]: self.complete_action(
                aid,
                atype,
            )
        )
        buttons.addWidget(done)

        dismiss = QPushButton("Dismiss")
        dismiss.setObjectName("Danger")
        dismiss.setCursor(Qt.PointingHandCursor)
        dismiss.clicked.connect(
            lambda checked=False, aid=action["id"]: self.dismiss_action(aid)
        )
        buttons.addWidget(dismiss)

        layout.addLayout(buttons)
        return card

    def refresh(self):
        actions = self.db.cursor.execute("""
            SELECT
                a.*,
                COALESCE(
                    NULLIF(p.company_name, ''),
                    p.domain,
                    a.domain
                ) AS company_name
            FROM automation_actions a
            LEFT JOIN prospects p ON p.id = a.prospect_id
            WHERE a.status = 'OPEN'
            ORDER BY
                CASE a.priority
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    ELSE 3
                END,
                CASE WHEN a.due_date = '' THEN 1 ELSE 0 END,
                a.due_date ASC,
                a.created_at DESC
        """).fetchall()

        self._clear_layout(self.actions_layout)

        n = len(actions)
        self.count.setText(f"{n} open action" if n == 1 else f"{n} open actions")

        if not actions:
            empty = QLabel("No actions require your attention right now.")
            empty.setObjectName("Subtitle")
            empty.setAlignment(Qt.AlignCenter)
            self.actions_layout.addStretch()
            self.actions_layout.addWidget(empty)
            self.actions_layout.addStretch()
            return

        for action in actions:
            self.actions_layout.addWidget(self._action_card(action))

        self.actions_layout.addStretch()

    def complete_action(self, action_id, action_type=None):
        if action_type == "CAMPAIGN_STEP_DUE":
            result = self.campaign_execution.complete_action(
                action_id
            )

            if result.get("completed"):
                next_step = result.get("next_step")

                if next_step:
                    print(
                        "CAMPAIGN ACTION COMPLETED: "
                        f"next step = {next_step}"
                    )
                else:
                    print(
                        "CAMPAIGN ACTION COMPLETED: "
                        "campaign sequence finished"
                    )

            self.refresh()
            return

        self.db.cursor.execute("""
            UPDATE automation_actions
            SET status = 'COMPLETED', completed_at = datetime('now')
            WHERE id = ? AND status = 'OPEN'
        """, (action_id,))
        self.db.connection.commit()
        self.refresh()

    def prepare_campaign_email(self, action_id):
        """
        Create an editable Outlook draft for a campaign action.

        This deliberately uses Outlook's Draft/Display workflow:
        - recipient, subject and body are populated;
        - the message is displayed for review;
        - nothing is sent automatically.
        """
        print(
            f"PREPARE EMAIL CLICKED: action_id={action_id}"
        )

        action = self.db.cursor.execute(
            """
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
            WHERE a.id = ?
              AND a.status = 'OPEN'
              AND a.action_type = 'CAMPAIGN_STEP_DUE'
            LIMIT 1
            """,
            (action_id,),
        ).fetchone()

        if not action:
            print(
                f"Could not prepare campaign email: action {action_id} not found."
            )
            return

        to_address = (action["contact_email"] or "").strip()
        contact_name_from_history = (action["contact_name"] or "").strip()

        # Existing campaign actions may have been generated before the
        # contact lookup was added. Recover the recipient from Outlook's
        # email history without recreating or duplicating the action.
        if not to_address and action["domain"]:
            contact = self.db.cursor.execute(
                """
                SELECT
                    recipient_name,
                    recipient_email
                FROM emails
                WHERE lower(domain) = ?
                  AND trim(recipient_email) <> ''
                  AND lower(recipient_email) NOT LIKE '%@cypet.eu'
                ORDER BY sent_date DESC, id DESC
                LIMIT 1
                """,
                (action["domain"].strip().lower(),),
            ).fetchone()

            if contact:
                to_address = (
                    contact["recipient_email"] or ""
                ).strip().lower()

                if not contact_name_from_history:
                    contact_name_from_history = (
                        contact["recipient_name"] or ""
                    ).strip()

        if not to_address:
            print(
                "Could not prepare campaign email: "
                f"no contact email is available for {action['domain']}."
            )
            return

        campaign = self.db.cursor.execute(
            """
            SELECT name
            FROM campaigns
            WHERE id = ?
            LIMIT 1
            """,
            (action["campaign_id"],),
        ).fetchone()

        step = self.db.cursor.execute(
            """
            SELECT
                step_number,
                name,
                subject_template,
                body_template
            FROM campaign_steps
            WHERE id = ?
            LIMIT 1
            """,
            (action["campaign_step_id"],),
        ).fetchone()

        if not step:
            print(
                "Could not prepare campaign email: campaign step not found."
            )
            return

        contact_name = (
            contact_name_from_history
            or action["contact_name"]
            or to_address.split("@")[0]
            or "there"
        )

        company = (
            action["company_name"]
            or action["domain"]
            or ""
        )

        # Build the commercial context from the actual Outlook history.
        # We do not send anything and we do not alter the stored history.
        context = self._get_outlook_topic_context(
            to_address=to_address,
            domain=action["domain"] or "",
        )

        topic = context["topic"]
        last_sent_subject = context["last_sent_subject"]
        last_sent_body = context["last_sent_body"]
        last_reply_subject = context["last_reply_subject"]
        last_reply_body = context["last_reply_body"]

        thread_messages = self._get_outlook_conversation_thread(
            to_address=to_address,
            domain=action["domain"] or "",
            context=context,
        )

        intelligence = self.conversation_intelligence.analyze_thread(
            contact_name=contact_name,
            company=company,
            messages=thread_messages,
            fallback_sent_subject=last_sent_subject,
            fallback_sent_body=last_sent_body,
            fallback_reply_subject=last_reply_subject,
            fallback_reply_body=last_reply_body,
        )

        # Persist an explicit customer-requested contact date in the campaign.
        # This is only done when the conversation intelligence has detected a
        # concrete commitment; otherwise the campaign remains unchanged.
        commitment = intelligence.get("next_contact_commitment") or ""
        if commitment == "MID-SEPTEMBER" and action["campaign_id"]:
            try:
                from modules.campaign_engine import CampaignEngine
                CampaignEngine(self.db).set_customer_commitment(
                    campaign_id=action["campaign_id"],
                    prospect_id=action["prospect_id"],
                    commitment_type="CUSTOMER_REQUESTED_FOLLOW_UP",
                    commitment_date=f"{datetime.now().year}-09-15",
                    note="Customer requested reconnection in mid-September.",
                    source="conversation_intelligence",
                )
                print(
                    "CUSTOMER COMMITMENT SAVED: "
                    f"{commitment} -> {datetime.now().year}-09-15"
                )
            except Exception as exc:
                print(f"Could not save customer commitment: {exc}")

        # The commercial topic in the real conversation has priority over
        # the generic campaign step name. This keeps the follow-up attached
        # to the subject actually discussed with the customer.
        conversation_subject = (
            last_reply_subject
            or last_sent_subject
            or ""
        ).strip()

        if conversation_subject:
            subject = conversation_subject
        else:
            subject = (
                step["subject_template"]
                or step["name"]
                or "Follow-up"
            )

        body_template = (
            step["body_template"]
            or ""
        ).strip()

        # If a customer reply exists, its language wins. Otherwise use the
        # language of the latest available communication.
        language = intelligence["language"]

        if body_template:
            body = self._render_campaign_template(
                body_template,
                contact_name=contact_name,
                company=company,
                domain=action["domain"] or "",
                campaign_name=campaign["name"] if campaign else "",
                step_name=step["name"],
                topic=intelligence["topic"],
                last_sent_subject=last_sent_subject,
                last_reply_subject=last_reply_subject,
            )
        else:
            body = self._intelligence_campaign_email(
                intelligence=intelligence,
                language=language,
            )

        try:
            # Prefer an already-running Outlook session.
            try:
                outlook = win32com.client.GetActiveObject(
                    "Outlook.Application"
                )
                print("Using existing Outlook session.")
            except Exception:
                outlook = win32com.client.Dispatch(
                    "Outlook.Application"
                )
                print("Started Outlook through COM.")

            mail = outlook.CreateItem(0)

            mail.To = to_address
            mail.Subject = subject

            # IMPORTANT:
            # Display first so Outlook itself inserts Sandro's configured
            # default signature. We then insert our generated message ABOVE
            # that signature instead of replacing it.
            mail.Display(False)

            # Use Outlook's Word editor to insert the generated text at the
            # very beginning of the message. This is more reliable than
            # replacing HTMLBody: Outlook keeps its native signature,
            # including formatting, images and links, exactly as configured.
            inspector = mail.GetInspector
            editor = inspector.WordEditor

            # Outlook's WordEditor is itself the editable Word document.
            # Do not access editor.Document: that property is not exposed
            # consistently by the Outlook COM wrapper.
            start_range = editor.Range(0, 0)
            start_range.InsertBefore(
                body.strip() + "\r\n\r\n"
            )

            # Save as a real editable Outlook draft. Nothing is sent.
            mail.Save()

            print(
                f"CAMPAIGN EMAIL DRAFT OPENED: "
                f"{to_address} | {subject}"
            )
            print(
                f"COMMERCIAL TOPIC (BODY ONLY): "
                f"{intelligence['topic'] or 'not identified'}"
            )
            print(
                f"CONVERSATION CONTEXT STATUS: "
                f"{intelligence['context_status']}"
            )
            print(
                f"CONVERSATION CONFIDENCE: "
                f"{intelligence['confidence']}"
            )
            print(
                f"THREAD MESSAGES: "
                f"{intelligence['thread_messages']}"
            )
            print(
                f"CUSTOMER MESSAGES: "
                f"{intelligence['customer_messages']}"
            )
            print(
                f"CYPET MESSAGES: "
                f"{intelligence['cypet_messages']}"
            )
            print("THREAD CLASSIFICATION:")
            for idx, msg in enumerate(
                intelligence.get("thread", []),
                start=1,
            ):
                preview = " ".join(str(msg.get("body", "")).split())[:120]
                print(
                    f"  [{idx}] {msg['direction'].upper()} | "
                    f"{msg.get('subject', '')[:100]}"
                )
                print(f"      BODY: {preview}")
            print("THREAD BODY CHECK: end of diagnostic")
            print(
                f"CONVERSATION LANGUAGE: {intelligence['language']}"
            )
            print(
                f"CUSTOMER POSITION: {intelligence['customer_position']}"
            )
            print(
                f"OPEN POINT: {intelligence['open_point']}"
            )
            print(
                f"NEXT OBJECTIVE: {intelligence['next_objective']}"
            )
            print(
                f"WHAT CYPET PROPOSED: "
                f"{intelligence['what_cypet_proposed'][:240]}"
            )
            print(
                f"CAMPAIGN BODY LENGTH: {len(body)} characters"
            )
            print(
                f"CAMPAIGN GENERATED TEXT: "
                f"{body[:180].replace(chr(10), ' ')}"
            )

        except Exception as exc:
            print(
                "Could not prepare campaign email: "
                f"{type(exc).__name__}: {exc}"
            )

    @staticmethod
    def _render_campaign_template(
        template,
        contact_name="",
        company="",
        domain="",
        campaign_name="",
        step_name="",
        topic="",
        last_sent_subject="",
        last_reply_subject="",
    ):
        replacements = {
            "{{contact_name}}": contact_name,
            "{{company}}": company,
            "{{domain}}": domain,
            "{{campaign_name}}": campaign_name,
            "{{step_name}}": step_name,
            "{{topic}}": topic,
            "{{last_sent_subject}}": last_sent_subject,
            "{{last_reply_subject}}": last_reply_subject,
        }

        result = template

        for token, value in replacements.items():
            result = result.replace(token, value or "")

        return result

    @staticmethod
    def _intelligence_campaign_email(intelligence, language):
        topic = (intelligence.get("topic") or "").strip()
        confidence = intelligence.get("confidence", "LOW")
        commitment = (intelligence.get("next_contact_commitment") or "").strip()
        position = (intelligence.get("customer_position") or "").lower()

        # If the customer explicitly requested a later contact date, the
        # assistant must respect it. Do not create a generic "checking in"
        # message that ignores the commitment.
        if commitment == "MID-SEPTEMBER":
            if language == "IT":
                return (
                    "Buongiorno Fausto,\n\n"
                    "come concordato, ci risentiamo a metà settembre.\n\n"
                    "Nel frattempo resto a disposizione per qualsiasi necessità.\n\n"
                    "Buon proseguimento e a presto."
                )
            return (
                "Hello Fausto,\n\n"
                "as agreed, I will get back in touch with you in mid-September.\n\n"
                "In the meantime, please feel free to contact me if anything is needed.\n\n"
                "Best regards."
            )

        # Low confidence: do not invent a topic or an agreed next step.
        if confidence == "LOW":
            if language == "IT":
                return (
                    "Buongiorno,\n\n"
                    "riprendo la nostra conversazione e volevo verificare "
                    "come possiamo procedere.\n\n"
                    "Se per te va bene, possiamo sentirci per un breve confronto."
                )
            return (
                "Hello,\n\n"
                "I am following up on our conversation and wanted to check "
                "how we can move forward.\n\n"
                "If convenient, we can arrange a short call."
            )

        accepted = "positively accepted" in position

        if language == "IT":
            if accepted:
                return (
                    "Buongiorno,\n\n"
                    "riprendo quanto ci siamo detti e il prossimo passo che abbiamo concordato"
                    + (f" in merito a {topic}." if topic else ".")
                    + "\n\n"
                    "Come anticipato, sono a disposizione per procedere e definire insieme i prossimi punti.\n\n"
                    "Se per te va bene, possiamo sentirci e fissare il prossimo passaggio."
                )

            return (
                "Buongiorno,\n\n"
                "riprendo la nostra conversazione"
                + (f" in merito a {topic}." if topic else ".")
                + "\n\n"
                "Vorrei capire come procedere e se ci sono ancora punti da approfondire da parte nostra.\n\n"
                "Se per te va bene, possiamo sentirci per un breve confronto."
            )

        if accepted:
            return (
                "Hello,\n\n"
                "I am following up on our discussion and on the next step we agreed"
                + (f" regarding {topic}." if topic else ".")
                + "\n\n"
                "As discussed, I am available to move forward and define the next points together.\n\n"
                "If convenient, we can arrange a short call and agree on the next step."
            )

        return (
            "Hello,\n\n"
            "I am following up on our conversation"
            + (f" regarding {topic}." if topic else ".")
            + "\n\n"
            "I would like to understand how we can move forward and whether there are any points we should clarify from our side.\n\n"
            "If convenient, we can arrange a short call."
        )


    @staticmethod
    def _context_aware_campaign_email(
        contact_name,
        company,
        topic,
        last_sent_subject,
        last_sent_body,
        last_reply_subject,
        last_reply_body,
        step_name,
    ):
        greeting = (
            f"Hi {contact_name},"
            if contact_name
            else "Hello,"
        )

        topic_text = topic or last_sent_subject or "our previous discussion"

        # Use only a short, clean excerpt as context. The full history is
        # never dumped into the outgoing message.
        reply_context = (
            last_reply_body.strip()
            if last_reply_body
            else ""
        )

        if len(reply_context) > 500:
            reply_context = reply_context[:500].rsplit(" ", 1)[0] + "..."

        sent_context = (
            last_sent_body.strip()
            if last_sent_body
            else ""
        )

        if len(sent_context) > 350:
            sent_context = sent_context[:350].rsplit(" ", 1)[0] + "..."

        company_line = (
            f" regarding {company}"
            if company
            else ""
        )

        lines = [
            greeting,
            "",
            f"I wanted to follow up on our previous discussion about {topic_text}{company_line}.",
        ]

        if reply_context:
            lines.extend([
                "",
                "In particular, I wanted to reconnect on the points raised in your last reply.",
            ])
        elif sent_context:
            lines.extend([
                "",
                "I wanted to reconnect on the points we discussed in our previous exchange.",
            ])

        lines.extend([
            "",
            "If this is still relevant, I would be glad to continue the discussion and see where we can support the project.",
            "",
            "Would it make sense to arrange a short call to discuss the next steps?",
        ])

        return "\n".join(lines)

    def _get_outlook_conversation_thread(
        self,
        to_address,
        domain,
        context=None,
    ):
        """
        Recover the complete available Outlook conversation.

        Preferred route:
        1. take the latest known Outlook item;
        2. ask Outlook for its Conversation object;
        3. enumerate the conversation table;
        4. resolve each EntryID back to a MailItem.

        Fallback:
        use the database-backed sent items plus the latest incoming messages
        already recovered by _get_outlook_topic_context().
        """
        context = context or {}
        target = (to_address or "").strip().lower()
        messages = []

        # Find a strong anchor item from the latest known sent message.
        anchor = None
        try:
            rows = self.db.cursor.execute(
                """
                SELECT outlook_id, subject, sent_date
                FROM emails
                WHERE (
                    lower(trim(recipient_email)) = ?
                    OR lower(trim(domain)) = ?
                )
                AND trim(recipient_email) <> ''
                ORDER BY sent_date DESC, id DESC
                LIMIT 10
                """,
                (
                    target,
                    (domain or "").strip().lower(),
                ),
            ).fetchall()

            for row in rows:
                try:
                    item = self.outlook.namespace.GetItemFromID(
                        row["outlook_id"]
                    )
                    anchor = item
                    break
                except Exception:
                    continue
        except Exception:
            pass

        if anchor is not None:
            try:
                conversation = anchor.GetConversation()
            except Exception:
                conversation = None

            if conversation is not None:
                try:
                    table = conversation.GetTable()
                    try:
                        table.Columns.Add("EntryID")
                    except Exception:
                        pass
                    try:
                        table.Columns.Add("StoreID")
                    except Exception:
                        pass

                    while not table.EndOfTable:
                        row = table.GetNextRow()
                        entry_id = str(row["EntryID"] or "").strip()
                        store_id = str(row["StoreID"] or "").strip()

                        if not entry_id:
                            continue

                        try:
                            if store_id:
                                item = self.outlook.namespace.GetItemFromID(
                                    entry_id,
                                    store_id,
                                )
                            else:
                                item = self.outlook.namespace.GetItemFromID(
                                    entry_id
                                )
                        except Exception:
                            continue

                        try:
                            sender = (
                                self.outlook.sender_smtp(item)
                                or str(item.SenderEmailAddress or "")
                            ).strip().lower()
                        except Exception:
                            sender = ""

                        try:
                            recipients = str(item.To or "").lower()
                        except Exception:
                            recipients = ""

                        sender_is_customer = (
                            bool(target)
                            and (sender == target or target in sender)
                        )
                        recipient_is_customer = (
                            bool(target)
                            and target in recipients
                        )

                        if sender_is_customer and not recipient_is_customer:
                            direction = "received"
                        elif recipient_is_customer and not sender_is_customer:
                            direction = "sent"
                        else:
                            continue

                        try:
                            date_value = (
                                item.ReceivedTime
                                if direction == "received"
                                else item.SentOn
                            )
                        except Exception:
                            date_value = None

                        messages.append({
                            "direction": direction,
                            "subject": str(item.Subject or ""),
                            "body": str(item.Body or ""),
                            "date": date_value,
                        })
                except Exception:
                    messages = []

        # Fallback / enrichment from the known context.
        if not messages:
            if context.get("last_sent_subject") or context.get("last_sent_body"):
                messages.append({
                    "direction": "sent",
                    "subject": context.get("last_sent_subject", ""),
                    "body": context.get("last_sent_body", ""),
                    "date": None,
                })

            if context.get("last_reply_subject") or context.get("last_reply_body"):
                messages.append({
                    "direction": "received",
                    "subject": context.get("last_reply_subject", ""),
                    "body": context.get("last_reply_body", ""),
                    "date": None,
                })

        # Sort chronologically where Outlook supplied dates. Keep stable order
        # for fallback records with no date.
        messages.sort(
            key=lambda m: (
                m.get("date") is None,
                m.get("date") or "",
            )
        )

        return messages

    def _get_outlook_topic_context(self, to_address, domain):
        """
        Recover the commercial topic from the real Outlook conversation
        history. The current database stores subject/recipient/EntryID;
        Outlook provides the actual message body and conversation thread.
        """
        result = {
            "topic": "",
            "last_sent_subject": "",
            "last_sent_body": "",
            "last_reply_subject": "",
            "last_reply_body": "",
        }

        sent_rows = self.db.cursor.execute(
            """
            SELECT
                outlook_id,
                recipient_email,
                subject,
                sent_date
            FROM emails
            WHERE (
                lower(trim(recipient_email)) = ?
                OR lower(trim(domain)) = ?
            )
            AND trim(recipient_email) <> ''
            ORDER BY sent_date DESC, id DESC
            LIMIT 10
            """,
            (
                (to_address or "").strip().lower(),
                (domain or "").strip().lower(),
            ),
        ).fetchall()

        sent_items = []

        for row in sent_rows:
            try:
                item = self.outlook.namespace.GetItemFromID(
                    row["outlook_id"]
                )
                subject = str(item.Subject or row["subject"] or "").strip()
                body = str(item.Body or "").strip()

                sent_items.append({
                    "subject": subject,
                    "body": body,
                    "sent_date": row["sent_date"],
                    "conversation_id": self._outlook_conversation_id(item),
                })
            except Exception:
                continue

        if sent_items:
            latest = sent_items[0]
            result["last_sent_subject"] = latest["subject"]
            result["last_sent_body"] = self._clean_outlook_body(
                latest["body"]
            )

            result["topic"] = self._normalize_topic(
                latest["subject"]
            )

        # Look for a recent incoming reply from the same contact. We use
        # the same subject/conversation matching principle already used by
        # the reply automation engine.
        target = (to_address or "").strip().lower()

        try:
            for mail in self.outlook.get_last_messages(200):
                try:
                    sender = (
                        self.outlook.sender_smtp(mail)
                        or ""
                    ).strip().lower()

                    if sender != target:
                        continue

                    subject = str(mail.Subject or "").strip()

                    if not subject:
                        continue

                    inbox_conversation = (
                        self._outlook_conversation_id(mail)
                    )

                    matched_sent = None

                    for sent in sent_items:
                        if (
                            inbox_conversation
                            and sent["conversation_id"]
                            and inbox_conversation
                            == sent["conversation_id"]
                        ):
                            matched_sent = sent
                            break

                    if matched_sent:
                        result["last_reply_subject"] = subject
                        result["last_reply_body"] = (
                            self._clean_outlook_body(
                                str(mail.Body or "")
                            )
                        )
                        result["topic"] = self._normalize_topic(
                            matched_sent["subject"]
                            or subject
                        )
                        break

                except Exception:
                    continue

        except Exception:
            pass

        return result

    @staticmethod
    def _outlook_conversation_id(mail):
        try:
            return str(
                mail.ConversationID or ""
            ).strip()
        except Exception:
            return ""

    @staticmethod
    def _normalize_topic(subject):
        subject = (subject or "").strip()

        subject = re.sub(
            r"^(?:(?:RE|FW|FWD)\s*:\s*)+",
            "",
            subject,
            flags=re.IGNORECASE,
        )

        return subject.strip()

    @staticmethod
    def _clean_outlook_body(body):
        text = (body or "").replace("\r\n", "\n").replace("\r", "\n")

        # Remove common quoted-reply separators.
        markers = [
            "\n-----Original Message-----",
            "\nFrom:",
            "\nSent:",
        ]

        for marker in markers:
            if marker in text:
                text = text.split(marker, 1)[0]

        return text.strip()

    @staticmethod
    def _plain_text_to_html(text):
        escaped = escape(text or "")
        return (
            "<div style=\"font-family:Calibri,Arial,sans-serif;"
            "font-size:11pt;line-height:1.45;\">"
            + escaped.replace("\n", "<br>")
            + "</div><br>"
        )

    @staticmethod
    def _insert_before_signature(existing_html, message_html):
        if not existing_html:
            return (
                "<html><body>"
                + message_html
                + "</body></html>"
            )

        match = re.search(
            r"(<body\b[^>]*>)",
            existing_html,
            flags=re.IGNORECASE,
        )

        if match:
            return (
                existing_html[:match.end()]
                + message_html
                + existing_html[match.end():]
            )

        return message_html + existing_html


    def dismiss_action(self, action_id):
        self.db.cursor.execute("""
            UPDATE automation_actions
            SET status = 'DISMISSED'
            WHERE id = ? AND status = 'OPEN'
        """, (action_id,))
        self.db.connection.commit()
        self.refresh()

    def open_email(self, entry_id):
        try:
            mail = self.outlook.namespace.GetItemFromID(entry_id)
            mail.Display()
        except Exception as exc:
            print(f"Could not open Outlook email: {exc}")

    def refresh_data(self):
        self.refresh()

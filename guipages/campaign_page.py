from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QLineEdit,
    QScrollArea,
    QStackedWidget,
)


class CampaignPage(QWidget):
    """
    Campaign management page.

    V5:
    - Separate Campaigns and Select Prospects pages with QStackedWidget.
    - No widget is destroyed/recreated during Back navigation.
    - Campaign and prospect lists use real scrollable areas.
    - No emails are sent from this page.
    """

    def __init__(self):
        super().__init__()

        from modules.database import Database
        from modules.campaign_engine import CampaignEngine

        self.db = Database()
        self.engine = CampaignEngine(self.db)

        self.current_campaign_id = None

        self.setStyleSheet("""
            QFrame#Panel {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }

            QLabel#Title {
                color: #1F2937;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#PanelTitle {
                color: #1F2937;
                font-size: 14pt;
                font-weight: 700;
            }

            QLabel#Meta {
                color: #6B7280;
                font-size: 10pt;
            }

            QLabel#Status {
                color: #0EA5E9;
                font-size: 10pt;
                font-weight: 700;
            }

            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: white;
                padding: 4px;
            }

            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E5E7EB;
            }

            QListWidget::item:selected {
                background: #EFF6FF;
                color: #1F2937;
            }

            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                padding: 8px;
                background: white;
            }

            QPushButton#Primary {
                background: #0EA5E9;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 16px;
                font-weight: 700;
            }

            QPushButton#Primary:hover {
                background: #0284C7;
            }

            QPushButton#Secondary {
                background: white;
                color: #1F2937;
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                padding: 9px 16px;
            }
        """)

        self.build_ui()
        self.refresh_campaigns()

    # ---------------------------------------------------------
    # MAIN UI
    # ---------------------------------------------------------

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        self.title = QLabel("Campaigns")
        self.title.setObjectName("Title")
        root.addWidget(self.title)

        self.panel = QFrame()
        self.panel.setObjectName("Panel")

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)

        self.views = QStackedWidget()
        panel_layout.addWidget(self.views, 1)

        root.addWidget(self.panel, 1)

        self.build_campaign_view()
        self.build_target_view()
        self.build_review_view()
        self.build_activation_view()

        self.views.setCurrentWidget(self.campaign_view)

    # ---------------------------------------------------------
    # CAMPAIGN VIEW
    # ---------------------------------------------------------

    def build_campaign_view(self):
        self.campaign_view = QWidget()
        layout = QVBoxLayout(self.campaign_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()

        label = QLabel("Campaigns")
        label.setObjectName("PanelTitle")

        refresh = QPushButton("Refresh")
        refresh.setObjectName("Secondary")
        refresh.clicked.connect(self.refresh_campaigns)

        header.addWidget(label)
        header.addStretch()
        header.addWidget(refresh)

        layout.addLayout(header)

        self.campaign_list = QListWidget()
        self.campaign_list.setMinimumHeight(160)
        self.campaign_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.campaign_list.currentItemChanged.connect(
            self.show_campaign_details
        )

        layout.addWidget(self.campaign_list, 2)

        self.detail_title = QLabel("Select a campaign")
        self.detail_title.setObjectName("PanelTitle")

        self.detail_status = QLabel("")
        self.detail_status.setObjectName("Status")

        self.detail_meta = QLabel("")
        self.detail_meta.setObjectName("Meta")
        self.detail_meta.setWordWrap(True)

        layout.addWidget(self.detail_title)
        layout.addWidget(self.detail_status)
        layout.addWidget(self.detail_meta)

        self.step_list = QListWidget()
        self.step_list.setMinimumHeight(120)
        self.step_list.setMaximumHeight(190)
        self.step_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        layout.addWidget(self.step_list, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.select_prospects_button = QPushButton(
            "Select Prospects"
        )
        self.select_prospects_button.setObjectName("Primary")
        self.select_prospects_button.setEnabled(False)
        self.select_prospects_button.clicked.connect(
            self.show_target_view
        )

        buttons.addWidget(self.select_prospects_button)
        layout.addLayout(buttons)

        self.views.addWidget(self.campaign_view)

    def refresh_campaigns(self):
        self.campaign_list.blockSignals(True)
        self.campaign_list.clear()
        self.campaign_list.blockSignals(False)

        campaigns = self.engine.get_campaigns()

        if not campaigns:
            self.current_campaign_id = None
            self.detail_title.setText("No campaigns")
            self.detail_status.setText("")
            self.detail_meta.setText(
                "Create a campaign before selecting a target."
            )
            self.step_list.clear()
            self.select_prospects_button.setEnabled(False)
            return

        for campaign in campaigns:
            item = QListWidgetItem()

            item.setData(Qt.UserRole, campaign["id"])

            members = campaign["members"] or 0
            active = campaign["active_members"] or 0

            item.setText(
                f"{campaign['name']}  ·  "
                f"{campaign['status']}  ·  "
                f"{members} prospects"
            )

            item.setToolTip(
                f"Active prospects: {active}"
            )

            self.campaign_list.addItem(item)

        self.campaign_list.setCurrentRow(0)

    def show_campaign_details(self, current, previous=None):
        if current is None:
            return

        campaign_id = current.data(Qt.UserRole)
        self.current_campaign_id = campaign_id

        summary = self.engine.campaign_summary(campaign_id)

        if not summary:
            return

        campaign = summary["campaign"]

        self.detail_title.setText(campaign["name"])
        self.detail_status.setText(campaign["status"])

        self.detail_meta.setText(
            f"{campaign['description'] or 'No description'}\n\n"
            f"Prospects: {summary['total']}   ·   "
            f"Active: {summary['active']}   ·   "
            f"Replies: {summary['replied']}   ·   "
            f"Completed: {summary['completed']}"
        )

        self.step_list.clear()

        for step in self.engine.get_steps(campaign_id):
            item = QListWidgetItem(
                f"{step['step_number']}. "
                f"{step['name']}  ·  "
                f"+{step['delay_days']} days"
            )
            self.step_list.addItem(item)

        self.select_prospects_button.setEnabled(True)

    # ---------------------------------------------------------
    # TARGET VIEW
    # ---------------------------------------------------------

    def build_target_view(self):
        self.target_view = QWidget()
        layout = QVBoxLayout(self.target_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QHBoxLayout()

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("Secondary")
        self.back_button.setFixedWidth(100)
        self.back_button.clicked.connect(
            self.show_campaign_view
        )

        self.target_title = QLabel("Select Prospects")
        self.target_title.setObjectName("PanelTitle")
        self.target_title.setWordWrap(True)

        header.addWidget(self.back_button)
        header.addSpacing(10)
        header.addWidget(self.target_title, 1)

        layout.addLayout(header)

        info = QLabel(
            "Select the prospects that should enter this campaign. "
            "No email will be sent at this stage."
        )
        info.setObjectName("Meta")
        info.setWordWrap(True)
        layout.addWidget(info)

        filter_row = QHBoxLayout()

        self.target_search = QLineEdit()
        self.target_search.setPlaceholderText(
            "Search company, domain, name or email..."
        )
        self.target_search.textChanged.connect(
            self.filter_targets
        )

        select_all = QPushButton("Select visible")
        select_all.setObjectName("Secondary")
        select_all.clicked.connect(
            self.select_visible_targets
        )

        clear_all = QPushButton("Clear")
        clear_all.setObjectName("Secondary")
        clear_all.clicked.connect(
            self.clear_targets
        )

        filter_row.addWidget(self.target_search, 1)
        filter_row.addWidget(select_all)
        filter_row.addWidget(clear_all)

        layout.addLayout(filter_row)

        # A dedicated scroll area prevents the prospect list from
        # consuming the whole window and guarantees vertical scrolling.
        self.target_scroll = QScrollArea()
        self.target_scroll.setWidgetResizable(True)
        self.target_scroll.setFrameShape(QFrame.NoFrame)
        self.target_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        target_container = QWidget()
        target_container_layout = QVBoxLayout(
            target_container
        )
        target_container_layout.setContentsMargins(0, 0, 0, 0)

        self.target_list = QListWidget()
        self.target_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.target_list.itemChanged.connect(
            self.update_target_count
        )

        target_container_layout.addWidget(
            self.target_list, 1
        )

        self.target_scroll.setWidget(
            target_container
        )

        layout.addWidget(self.target_scroll, 1)

        footer = QHBoxLayout()

        self.target_count = QLabel("Selected: 0")
        self.target_count.setObjectName("Status")

        footer.addWidget(self.target_count)
        footer.addStretch()

        enroll = QPushButton("Add to Campaign")
        enroll.setObjectName("Primary")
        enroll.clicked.connect(
            self.enroll_selected_targets
        )

        review = QPushButton("Review Target")
        review.setObjectName("Secondary")
        review.clicked.connect(
            self.show_review_view
        )

        footer.addWidget(review)
        footer.addWidget(enroll)

        layout.addLayout(footer)

        self.views.addWidget(self.target_view)

    def show_target_view(self):
        if not self.current_campaign_id:
            return

        campaign = self.engine._campaign(
            self.current_campaign_id
        )

        if not campaign:
            return

        self.target_title.setText(
            f"Select Prospects  ·  {campaign['name']}"
        )

        self.target_search.clear()
        self.load_targets()

        self.views.setCurrentWidget(
            self.target_view
        )

    def show_campaign_view(self):
        # IMPORTANT: switch the existing page instead of destroying
        # and recreating widgets. This eliminates the old Back-button
        # overlap/ghost-widget problem.
        self.views.setCurrentWidget(
            self.campaign_view
        )

        self.refresh_campaigns()

    # ---------------------------------------------------------
    # REVIEW TARGET VIEW
    # ---------------------------------------------------------

    def build_review_view(self):
        self.review_view = QWidget()
        layout = QVBoxLayout(self.review_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()

        back = QPushButton("← Back")
        back.setObjectName("Secondary")
        back.setFixedWidth(100)
        back.clicked.connect(self.show_target_view)

        self.review_title = QLabel("Review Target")
        self.review_title.setObjectName("PanelTitle")
        self.review_title.setWordWrap(True)

        header.addWidget(back)
        header.addSpacing(10)
        header.addWidget(self.review_title, 1)

        layout.addLayout(header)

        self.review_meta = QLabel("")
        self.review_meta.setObjectName("Meta")
        self.review_meta.setWordWrap(True)
        layout.addWidget(self.review_meta)

        self.review_scroll = QScrollArea()
        self.review_scroll.setWidgetResizable(True)
        self.review_scroll.setFrameShape(QFrame.NoFrame)
        self.review_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        review_container = QWidget()
        review_container_layout = QVBoxLayout(
            review_container
        )
        review_container_layout.setContentsMargins(0, 0, 0, 0)

        self.review_prospect_list = QListWidget()
        self.review_prospect_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        review_container_layout.addWidget(
            self.review_prospect_list, 1
        )

        self.review_scroll.setWidget(
            review_container
        )

        layout.addWidget(self.review_scroll, 1)

        sequence_label = QLabel("Campaign sequence")
        sequence_label.setObjectName("PanelTitle")
        layout.addWidget(sequence_label)

        self.review_sequence_list = QListWidget()
        self.review_sequence_list.setMaximumHeight(170)
        self.review_sequence_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        layout.addWidget(self.review_sequence_list)

        footer = QHBoxLayout()

        back_targets = QPushButton("Back to Prospects")
        back_targets.setObjectName("Secondary")
        back_targets.clicked.connect(
            self.show_target_view
        )

        activate = QPushButton("Continue to Activation")
        activate.setObjectName("Primary")
        activate.clicked.connect(
            self.show_activation_confirmation
        )

        footer.addWidget(back_targets)
        footer.addStretch()
        footer.addWidget(activate)

        layout.addLayout(footer)

        self.views.addWidget(self.review_view)

    def show_review_view(self):
        if not self.current_campaign_id:
            return

        campaign = self.engine._campaign(
            self.current_campaign_id
        )

        if not campaign:
            return

        members = self.db.cursor.execute(
            """
            SELECT p.*
            FROM prospects p
            INNER JOIN campaign_members cm
                ON cm.prospect_id = p.id
            WHERE cm.campaign_id = ?
            ORDER BY p.id
            """,
            (self.current_campaign_id,),
        ).fetchall()

        if not members:
            QMessageBox.warning(
                self,
                "Review Target",
                "No prospects have been added to this campaign yet.",
            )
            return

        self.review_title.setText(
            f"Review Target  ·  {campaign['name']}"
        )

        self.review_meta.setText(
            f"Targeted prospects: {len(members)}\n"
            "Review the audience and sequence before activation. "
            "No emails will be sent from this screen."
        )

        self.review_prospect_list.clear()

        for row in members:
            item = QListWidgetItem(
                self._prospect_label(row)
            )
            item.setData(
                Qt.UserRole,
                self._row_value(row, "id")
            )
            self.review_prospect_list.addItem(item)

        self.review_sequence_list.clear()

        for step in self.engine.get_steps(
            self.current_campaign_id
        ):
            item = QListWidgetItem(
                f"{step['step_number']}. "
                f"{step['name']}  ·  "
                f"+{step['delay_days']} days"
            )
            self.review_sequence_list.addItem(item)

        self.views.setCurrentWidget(
            self.review_view
        )

    def show_activation_confirmation(self):
        if not self.current_campaign_id:
            return

        campaign = self.engine._campaign(
            self.current_campaign_id
        )

        if not campaign:
            return

        members = self.db.cursor.execute(
            """
            SELECT COUNT(*)
            FROM campaign_members
            WHERE campaign_id = ?
            """,
            (self.current_campaign_id,),
        ).fetchone()[0]

        if members == 0:
            QMessageBox.warning(
                self,
                "Activation",
                "The campaign has no prospects. Add at least one prospect first.",
            )
            return

        self.activation_title.setText(
            f"Activate Campaign  ·  {campaign['name']}"
        )

        self.activation_meta.setText(
            f"Target: {members} prospect(s)\n"
            f"Status: {campaign['status']}\n\n"
            "Activating the campaign will make its communication "
            "sequence eligible for execution by the Sales Assistant.\n"
            "No email will be sent by this activation click."
        )

        self.views.setCurrentWidget(
            self.activation_view
        )

    def activate_campaign(self):
        if not self.current_campaign_id:
            return

        campaign = self.engine._campaign(
            self.current_campaign_id
        )

        if not campaign:
            return

        if str(campaign["status"]).upper() == "ACTIVE":
            self.show_campaign_view()
            return

        members = self.db.cursor.execute(
            """
            SELECT COUNT(*)
            FROM campaign_members
            WHERE campaign_id = ?
            """,
            (self.current_campaign_id,),
        ).fetchone()[0]

        if members == 0:
            QMessageBox.warning(
                self,
                "Activation",
                "The campaign has no prospects. Add at least one prospect first.",
            )
            return

        try:
            activated = self.engine.activate_campaign(
                self.current_campaign_id
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Activation error",
                str(exc),
            )
            return

        if not activated:
            QMessageBox.warning(
                self,
                "Activation",
                "The campaign could not be activated.",
            )
            return

        QMessageBox.information(
            self,
            "Campaign activated",
            (
                f"{campaign['name']} is now ACTIVE.\n\n"
                "No email has been sent.\n"
                "The next step will be the campaign execution engine."
            ),
        )

        self.show_campaign_view()

    # ---------------------------------------------------------
    # ACTIVATION VIEW
    # ---------------------------------------------------------

    def build_activation_view(self):
        self.activation_view = QWidget()
        layout = QVBoxLayout(self.activation_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()

        back = QPushButton("← Back")
        back.setObjectName("Secondary")
        back.setFixedWidth(100)
        back.clicked.connect(self.show_review_view)

        self.activation_title = QLabel("Activate Campaign")
        self.activation_title.setObjectName("PanelTitle")
        self.activation_title.setWordWrap(True)

        header.addWidget(back)
        header.addSpacing(10)
        header.addWidget(self.activation_title, 1)

        layout.addLayout(header)

        warning = QFrame()
        warning.setStyleSheet("""
            QFrame {
                background: #FFF7ED;
                border: 1px solid #FDBA74;
                border-radius: 10px;
            }
        """)

        warning_layout = QVBoxLayout(warning)

        warning_title = QLabel("⚠ Activation control")
        warning_title.setStyleSheet(
            "font-size: 13pt; font-weight: 700; color: #9A3412;"
        )

        warning_text = QLabel(
            "Activation changes the campaign status from DRAFT to ACTIVE. "
            "It does not send an email."
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet(
            "color: #7C2D12;"
        )

        warning_layout.addWidget(warning_title)
        warning_layout.addWidget(warning_text)

        layout.addWidget(warning)

        self.activation_meta = QLabel("")
        self.activation_meta.setObjectName("Meta")
        self.activation_meta.setWordWrap(True)

        layout.addWidget(self.activation_meta)

        # Keep the activation controls in the visible content area.
        # Do not add a stretch here: the campaign/target views can impose
        # a larger minimum size on the stacked widget and push the footer
        # below the visible window.
        layout.addSpacing(20)

        footer = QHBoxLayout()

        cancel = QPushButton("Cancel")
        cancel.setObjectName("Secondary")
        cancel.clicked.connect(self.show_review_view)

        activate = QPushButton("Activate Campaign")
        activate.setObjectName("Primary")
        activate.clicked.connect(
            self.activate_campaign
        )

        footer.addWidget(cancel)
        footer.addStretch()
        footer.addWidget(activate)

        layout.addLayout(footer)

        self.views.addWidget(self.activation_view)

    # ---------------------------------------------------------
    # PROSPECT DATA
    # ---------------------------------------------------------

    def _get_prospects(self):
        columns = self.db.cursor.execute(
            "PRAGMA table_info(prospects)"
        ).fetchall()

        names = [row["name"] for row in columns]

        if "id" not in names:
            return []

        return self.db.cursor.execute(
            "SELECT * FROM prospects ORDER BY id"
        ).fetchall()

    @staticmethod
    def _row_value(row, name):
        try:
            return row[name]
        except Exception:
            return None

    def _prospect_label(self, row):
        company = (
            self._row_value(row, "company_name")
            or self._row_value(row, "company")
            or self._row_value(row, "domain")
            or "-"
        )

        name = (
            self._row_value(row, "contact_name")
            or self._row_value(row, "name")
            or self._row_value(row, "full_name")
            or ""
        )

        email = (
            self._row_value(row, "email")
            or self._row_value(row, "email_address")
            or ""
        )

        domain = self._row_value(row, "domain") or ""

        parts = [str(company)]

        if name and str(name) not in parts:
            parts.append(str(name))

        if email:
            parts.append(str(email))
        elif domain and str(domain) not in parts:
            parts.append(str(domain))

        return "  ·  ".join(parts)

    def load_targets(self):
        self.target_list.blockSignals(True)
        self.target_list.clear()
        self.target_list.blockSignals(False)

        rows = self._get_prospects()

        if not rows:
            self.target_list.addItem(
                "No prospects available."
            )
            self.target_count.setText("Selected: 0")
            return

        campaign_members = {
            row["prospect_id"]
            for row in self.db.cursor.execute(
                """
                SELECT prospect_id
                FROM campaign_members
                WHERE campaign_id = ?
                """,
                (self.current_campaign_id,),
            ).fetchall()
        }

        for row in rows:
            prospect_id = self._row_value(row, "id")

            item = QListWidgetItem(
                self._prospect_label(row)
            )

            item.setData(
                Qt.UserRole,
                prospect_id
            )

            item.setFlags(
                item.flags()
                | Qt.ItemIsUserCheckable
            )

            if prospect_id in campaign_members:
                item.setCheckState(Qt.Checked)
                item.setToolTip(
                    "Already enrolled in this campaign."
                )
            else:
                item.setCheckState(Qt.Unchecked)

            self.target_list.addItem(item)

        self.update_target_count()

    # ---------------------------------------------------------
    # TARGET FILTER / SELECTION
    # ---------------------------------------------------------

    def filter_targets(self, text):
        text = (text or "").strip().lower()

        for index in range(self.target_list.count()):
            item = self.target_list.item(index)

            visible = (
                not text
                or text in item.text().lower()
            )

            item.setHidden(not visible)

    def select_visible_targets(self):
        self.target_list.blockSignals(True)

        for index in range(self.target_list.count()):
            item = self.target_list.item(index)

            if not item.isHidden():
                item.setCheckState(Qt.Checked)

        self.target_list.blockSignals(False)
        self.update_target_count()

    def clear_targets(self):
        self.target_list.blockSignals(True)

        for index in range(self.target_list.count()):
            self.target_list.item(index).setCheckState(
                Qt.Unchecked
            )

        self.target_list.blockSignals(False)
        self.update_target_count()

    def update_target_count(self, item=None):
        selected = 0

        for index in range(self.target_list.count()):
            item = self.target_list.item(index)

            if item.checkState() == Qt.Checked:
                selected += 1

        self.target_count.setText(
            f"Selected: {selected}"
        )

    # ---------------------------------------------------------
    # ENROLL
    # ---------------------------------------------------------

    def enroll_selected_targets(self):
        prospect_ids = []

        for index in range(self.target_list.count()):
            item = self.target_list.item(index)

            if item.checkState() != Qt.Checked:
                continue

            prospect_id = item.data(Qt.UserRole)

            if prospect_id is not None:
                prospect_ids.append(prospect_id)

        if not prospect_ids:
            QMessageBox.warning(
                self,
                "Campaign",
                "Select at least one prospect.",
            )
            return

        try:
            enrolled = self.engine.enroll_prospects(
                self.current_campaign_id,
                prospect_ids,
            )

            QMessageBox.information(
                self,
                "Campaign target",
                (
                    f"{enrolled} prospect(s) added to the campaign.\n\n"
                    "No emails were sent."
                ),
            )

            self.load_targets()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Campaign error",
                str(exc),
            )

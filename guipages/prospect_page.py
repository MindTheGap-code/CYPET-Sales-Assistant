from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QDateEdit,
    QCheckBox,
    QScrollArea,
)

from modules.database import Database


class ProspectDialog(QDialog):
    def __init__(self, database, prospect_id, parent=None):
        super().__init__(parent)

        self.db = database
        self.prospect_id = prospect_id

        self.setWindowTitle("Prospect details")
        self.resize(980, 780)

        self.setStyleSheet("""
            QDialog {
                background: #F4F6F9;
            }

            QFrame#Card {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }

            QLabel#Title {
                color: #1F2937;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#SectionTitle {
                color: #374151;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#Caption {
                color: #6B7280;
                font-size: 10pt;
            }

            QLineEdit,
            QComboBox,
            QTextEdit {
                background: #F7F9FC;
                border: 1px solid #DCE3EA;
                border-radius: 8px;
                padding: 8px 10px;
            }

            QTableWidget {
                background: white;
                border: none;
                gridline-color: #EEF1F4;
                selection-background-color: #E8F6FB;
                selection-color: #1F2937;
            }

            QHeaderView::section {
                background: #F7F9FC;
                color: #6B7280;
                border: none;
                border-bottom: 1px solid #DCE3EA;
                padding: 8px;
                font-weight: 600;
            }

            QPushButton#Save {
                background: #00A3E0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: 600;
            }
        """)

        prospect = self.db.get_prospect(prospect_id)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(14)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("Prospect details")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.domain = QLabel(
            prospect["domain"] if prospect else "-"
        )
        self.domain.setObjectName("Caption")
        layout.addWidget(self.domain)

        layout.addWidget(QLabel("Company", objectName="Caption"))
        self.company = QLineEdit()
        self.company.setText(
            prospect["company_name"] if prospect else ""
        )
        layout.addWidget(self.company)

        layout.addWidget(QLabel("Industry", objectName="Caption"))
        self.industry = QComboBox()
        self.industry.addItems([
            "",
            "PET Packaging",
            "Beverage",
            "Pharma",
            "Cosmetics",
            "Home Care",
            "Partner",
            "Other",
        ])

        if prospect:
            index = self.industry.findText(prospect["industry"] or "")
            self.industry.setCurrentIndex(max(index, 0))

        layout.addWidget(self.industry)

        layout.addWidget(QLabel("Status", objectName="Caption"))
        self.status = QComboBox()
        self.status.addItems([
            "New",
            "Contacted",
            "Follow-up needed",
            "Qualified",
            "Customer",
        ])

        if prospect:
            index = self.status.findText(prospect["status"] or "New")
            self.status.setCurrentIndex(max(index, 0))

        layout.addWidget(self.status)

        layout.addWidget(QLabel("Notes", objectName="Caption"))
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Add notes about this prospect...")
        self.notes.setMinimumHeight(90)

        if prospect:
            self.notes.setPlainText(prospect["notes"] or "")

        layout.addWidget(self.notes)
        content_layout.addWidget(card)

        followup_card = QFrame()
        followup_card.setObjectName("Card")
        followup_layout = QVBoxLayout(followup_card)
        followup_layout.setContentsMargins(20, 16, 20, 16)
        followup_layout.setSpacing(8)

        followup_title = QLabel("Next action")
        followup_title.setObjectName("SectionTitle")
        followup_layout.addWidget(followup_title)

        followup_row = QHBoxLayout()
        followup_row.setSpacing(10)

        self.next_action_date = QDateEdit()
        self.next_action_date.setCalendarPopup(True)
        self.next_action_date.setDisplayFormat("dd/MM/yyyy")

        self.next_action_note = QLineEdit()
        self.next_action_note.setPlaceholderText(
            "What should be done next?"
        )

        self.no_next_action = QCheckBox("No date")
        self.no_next_action.setChecked(True)

        followup_row.addWidget(self.next_action_date)
        followup_row.addWidget(self.next_action_note, 1)
        followup_row.addWidget(self.no_next_action)

        followup_layout.addLayout(followup_row)
        content_layout.addWidget(followup_card)

        if prospect:
            saved_date = prospect["next_action_date"] or ""
            if saved_date:
                date = QDate.fromString(saved_date, "yyyy-MM-dd")
                if date.isValid():
                    self.next_action_date.setDate(date)
                    self.no_next_action.setChecked(False)
            else:
                self.no_next_action.setChecked(True)

            self.next_action_note.setText(
                prospect["next_action_note"] or ""
            )

        self.next_action_date.setEnabled(
            not self.no_next_action.isChecked()
        )
        self.no_next_action.toggled.connect(
            self.next_action_date.setDisabled
        )

        contacts_card = QFrame()
        contacts_card.setObjectName("Card")
        contacts_layout = QVBoxLayout(contacts_card)
        contacts_layout.setContentsMargins(20, 16, 20, 16)
        contacts_layout.setSpacing(8)

        contacts_title = QLabel("Contacts")
        contacts_title.setObjectName("SectionTitle")

        self.contacts_table = QTableWidget(0, 4)
        self.contacts_table.setHorizontalHeaderLabels([
            "Name",
            "Email",
            "Emails",
            "Last contact",
        ])
        self.contacts_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.contacts_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.contacts_table.verticalHeader().setVisible(False)
        self.contacts_table.setMinimumHeight(150)
        self.contacts_table.setMaximumHeight(190)

        contacts_header = self.contacts_table.horizontalHeader()
        contacts_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        contacts_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        contacts_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        contacts_header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        contacts_layout.addWidget(contacts_title)
        contacts_layout.addWidget(self.contacts_table)
        content_layout.addWidget(contacts_card)

        history_card = QFrame()
        history_card.setObjectName("Card")
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(20, 16, 20, 16)
        history_layout.setSpacing(8)

        history_top = QHBoxLayout()

        history_title = QLabel("Email history")
        history_title.setObjectName("SectionTitle")

        self.history_filter = QLabel("All contacts")
        self.history_filter.setObjectName("Caption")

        self.show_all_button = QPushButton("Show all")
        self.show_all_button.setObjectName("Secondary")
        self.show_all_button.setCursor(Qt.PointingHandCursor)

        history_top.addWidget(history_title)
        history_top.addStretch()
        history_top.addWidget(self.history_filter)
        history_top.addWidget(self.show_all_button)

        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels([
            "Date",
            "Recipient",
            "Subject",
        ])
        self.history_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setMinimumHeight(170)
        self.history_table.setMaximumHeight(230)

        history_header = self.history_table.horizontalHeader()
        history_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        history_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        history_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )

        history_layout.addLayout(history_top)
        history_layout.addWidget(self.history_table)
        content_layout.addWidget(history_card, 1)

        self.contacts_table.itemSelectionChanged.connect(
            self.contact_selected
        )
        self.show_all_button.clicked.connect(
            self.show_all_history
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )

        save_button = QPushButton("Save prospect")
        save_button.setObjectName("Save")
        buttons.addButton(
            save_button,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        buttons.rejected.connect(self.reject)
        save_button.clicked.connect(self.save)

        content_layout.addWidget(buttons)
        content_layout.addStretch()

        self.load_activity()

    def load_activity(self):
        domain = self.domain.text()

        contacts = self.db.get_prospect_contacts(domain)
        self.contacts_table.setRowCount(0)

        for contact in contacts:
            row = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row)

            values = [
                contact["recipient_name"] or "-",
                contact["recipient_email"] or "-",
                str(contact["email_count"]),
                str(contact["last_contact"] or "-")[:16],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        contact["recipient_email"],
                    )
                self.contacts_table.setItem(row, column, item)

        self.show_all_history()

    def show_all_history(self):
        domain = self.domain.text()
        self.history_filter.setText("All contacts")
        history = self.db.get_prospect_emails(domain, 100)
        self._populate_history(history)

    def contact_selected(self):
        row = self.contacts_table.currentRow()

        if row < 0:
            return

        email_item = self.contacts_table.item(row, 0)
        recipient_email = email_item.data(Qt.ItemDataRole.UserRole)

        if not recipient_email:
            return

        domain = self.domain.text()
        history = self.db.get_contact_emails(
            domain,
            recipient_email,
            100,
        )

        self.history_filter.setText(
            f"Filtered: {recipient_email}"
        )
        self._populate_history(history)

    def _populate_history(self, history):
        self.history_table.setRowCount(0)

        for email in history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            values = [
                str(email["sent_date"] or "-")[:16],
                email["recipient_name"] or email["recipient_email"] or "-",
                email["subject"] or "(No subject)",
            ]

            for column, value in enumerate(values):
                self.history_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

    def save(self):
        self.db.save_prospect(
            self.prospect_id,
            self.company.text(),
            self.industry.currentText(),
            self.status.currentText(),
            self.notes.toPlainText(),
            (
                ""
                if self.no_next_action.isChecked()
                else self.next_action_date.date().toString("yyyy-MM-dd")
            ),
            self.next_action_note.text(),
        )
        self.accept()


class ProspectPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.all_prospects = []

        self.setStyleSheet("""
            QFrame#Header,
            QFrame#Filters,
            QFrame#Results {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }

            QLabel#Title {
                color: #1F2937;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#Subtitle,
            QLabel#Caption {
                color: #6B7280;
                font-size: 10pt;
            }

            QLabel#Count {
                color: #00A3E0;
                font-size: 12pt;
                font-weight: 700;
            }

            QLineEdit {
                background: #F7F9FC;
                border: 1px solid #DCE3EA;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 20px;
            }

            QPushButton#Primary {
                background: #00A3E0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton#Primary:hover {
                background: #008FC4;
            }

            QPushButton#Secondary {
                background: #EEF4F8;
                color: #374151;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QTableWidget {
                background: white;
                border: none;
                gridline-color: #EEF1F4;
                selection-background-color: #E8F6FB;
                selection-color: #1F2937;
            }

            QHeaderView::section {
                background: #F7F9FC;
                color: #6B7280;
                border: none;
                border-bottom: 1px solid #DCE3EA;
                padding: 9px;
                font-weight: 600;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        header = QFrame()
        header.setObjectName("Header")

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(4)

        title = QLabel("Prospect")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Search and manage companies identified from your Outlook contacts."
        )
        subtitle.setObjectName("Subtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        root.addWidget(header)

        filters = QFrame()
        filters.setObjectName("Filters")

        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search company or domain...")
        self.search.setFixedHeight(38)

        search_button = QPushButton("Search")
        search_button.setObjectName("Primary")

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("Secondary")

        filters_layout.addWidget(self.search, 1)
        filters_layout.addWidget(search_button)
        filters_layout.addWidget(clear_button)

        root.addWidget(filters)

        results = QFrame()
        results.setObjectName("Results")

        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 16, 20, 16)
        results_layout.setSpacing(12)

        top = QHBoxLayout()

        result_title = QLabel("Prospects")
        result_title.setObjectName("Title")

        self.count = QLabel("0 companies")
        self.count.setObjectName("Count")

        self.edit_button = QPushButton("Open prospect")
        self.edit_button.setObjectName("Secondary")
        self.edit_button.setEnabled(False)

        top.addWidget(result_title)
        top.addStretch()
        top.addWidget(self.count)
        top.addWidget(self.edit_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Company / Domain",
            "Industry",
            "Status",
            "Contacts",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)

        table_header = self.table.horizontalHeader()
        table_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        table_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        table_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        table_header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        results_layout.addLayout(top)
        results_layout.addWidget(self.table)

        root.addWidget(results, 1)

        search_button.clicked.connect(self.search_prospects)
        clear_button.clicked.connect(self.clear_filters)
        self.search.returnPressed.connect(self.search_prospects)
        self.table.itemDoubleClicked.connect(
            lambda _: self.open_selected()
        )
        self.table.itemSelectionChanged.connect(
            self._selection_changed
        )
        self.edit_button.clicked.connect(self.open_selected)

        self.refresh_data()

    def refresh_data(self):
        self.all_prospects = self.db.get_prospects()
        self.populate_table(self.all_prospects)

    def search_prospects(self):
        query = self.search.text().strip()

        rows = self.db.get_prospects(search=query)
        self.populate_table(rows)

    def populate_table(self, rows):
        self.table.setRowCount(0)

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [
                row_data["company_name"] or row_data["domain"] or "-",
                row_data["industry"] or "-",
                row_data["status"] or "New",
                str(row_data["contacts"]),
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    row_data["id"],
                )
                self.table.setItem(row, column, item)

        self.count.setText(f"{len(rows)} companies")
        self._selection_changed()

    def _selection_changed(self):
        self.edit_button.setEnabled(
            self.table.currentRow() >= 0
        )

    def open_selected(self):
        row = self.table.currentRow()

        if row < 0:
            return

        item = self.table.item(row, 0)
        prospect_id = item.data(Qt.ItemDataRole.UserRole)

        dialog = ProspectDialog(
            self.db,
            prospect_id,
            self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()

    def clear_filters(self):
        self.search.clear()
        self.refresh_data()

from PySide6.QtCore import Qt
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
)

from modules.database import Database


class ProspectDialog(QDialog):
    def __init__(self, database, prospect_id, parent=None):
        super().__init__(parent)

        self.db = database
        self.prospect_id = prospect_id

        self.setWindowTitle("Prospect details")
        self.setMinimumWidth(520)

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
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

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
        self.notes.setMinimumHeight(120)

        if prospect:
            self.notes.setPlainText(prospect["notes"] or "")

        layout.addWidget(self.notes)

        root.addWidget(card)

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

        root.addWidget(buttons)

    def save(self):
        self.db.save_prospect(
            self.prospect_id,
            self.company.text(),
            self.industry.currentText(),
            self.status.currentText(),
            self.notes.toPlainText(),
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

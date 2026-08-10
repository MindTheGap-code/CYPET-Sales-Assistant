from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
)


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("CYPET", "SalesAssistant")

        self.setStyleSheet("""
            QFrame#Header,
            QFrame#Section {
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
                font-size: 12pt;
                font-weight: 700;
            }

            QLabel#Caption {
                color: #6B7280;
                font-size: 10pt;
            }

            QLineEdit {
                background: #F7F9FC;
                border: 1px solid #DCE3EA;
                border-radius: 8px;
                padding: 8px 10px;
            }

            QCheckBox {
                color: #374151;
                spacing: 8px;
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
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        header = QFrame()
        header.setObjectName("Header")

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(4)

        title = QLabel("Settings")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Configure the CYPET Sales Assistant application."
        )
        subtitle.setObjectName("Caption")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        root.addWidget(header)

        general = QFrame()
        general.setObjectName("Section")

        general_layout = QVBoxLayout(general)
        general_layout.setContentsMargins(20, 18, 20, 18)
        general_layout.setSpacing(12)

        general_title = QLabel("General")
        general_title.setObjectName("SectionTitle")

        self.company = QLineEdit()
        self.company.setPlaceholderText("Company name")

        self.user = QLineEdit()
        self.user.setPlaceholderText("User name")

        general_layout.addWidget(general_title)
        general_layout.addWidget(QLabel("Company", objectName="Caption"))
        general_layout.addWidget(self.company)
        general_layout.addWidget(QLabel("User", objectName="Caption"))
        general_layout.addWidget(self.user)

        root.addWidget(general)

        sync = QFrame()
        sync.setObjectName("Section")

        sync_layout = QVBoxLayout(sync)
        sync_layout.setContentsMargins(20, 18, 20, 18)
        sync_layout.setSpacing(12)

        sync_title = QLabel("Synchronization")
        sync_title.setObjectName("SectionTitle")

        self.outlook_check = QCheckBox(
            "Enable Outlook synchronization"
        )

        self.auto_sync = QCheckBox(
            "Synchronize automatically"
        )

        sync_layout.addWidget(sync_title)
        sync_layout.addWidget(self.outlook_check)
        sync_layout.addWidget(self.auto_sync)

        root.addWidget(sync)

        actions = QHBoxLayout()
        actions.addStretch()

        self.cancel = QPushButton("Cancel")
        self.cancel.setObjectName("Secondary")
        self.cancel.setCursor(Qt.PointingHandCursor)

        self.save = QPushButton("Save settings")
        self.save.setObjectName("Primary")
        self.save.setCursor(Qt.PointingHandCursor)

        actions.addWidget(self.cancel)
        actions.addWidget(self.save)

        root.addLayout(actions)
        root.addStretch()

        self.save.clicked.connect(self.save_settings)
        self.cancel.clicked.connect(self.load_settings)

        self.load_settings()

    def load_settings(self):
        self.company.setText(
            self.settings.value("company", "CYPET")
        )
        self.user.setText(
            self.settings.value("user", "Sandro Rasi")
        )

        self.outlook_check.setChecked(
            self.settings.value(
                "outlook_enabled", True, type=bool
            )
        )

        self.auto_sync.setChecked(
            self.settings.value(
                "auto_sync", True, type=bool
            )
        )

    def save_settings(self):
        self.settings.setValue(
            "company",
            self.company.text().strip() or "CYPET",
        )
        self.settings.setValue(
            "user",
            self.user.text().strip() or "Sandro Rasi",
        )
        self.settings.setValue(
            "outlook_enabled",
            self.outlook_check.isChecked(),
        )
        self.settings.setValue(
            "auto_sync",
            self.auto_sync.isChecked(),
        )
        self.settings.sync()

        self.save.setText("Saved ✓")

        self._restore_save_button()

    def _restore_save_button(self):
        from PySide6.QtCore import QTimer

        QTimer.singleShot(
            1800,
            lambda: self.save.setText("Save settings"),
        )

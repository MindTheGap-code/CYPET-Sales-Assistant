from PySide6.QtCore import Qt
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

        company = QLineEdit()
        company.setPlaceholderText("Company name")
        company.setText("CYPET")

        user = QLineEdit()
        user.setPlaceholderText("User name")
        user.setText("Sandro Rasi")

        general_layout.addWidget(general_title)
        general_layout.addWidget(QLabel("Company", objectName="Caption"))
        general_layout.addWidget(company)
        general_layout.addWidget(QLabel("User", objectName="Caption"))
        general_layout.addWidget(user)

        root.addWidget(general)

        sync = QFrame()
        sync.setObjectName("Section")

        sync_layout = QVBoxLayout(sync)
        sync_layout.setContentsMargins(20, 18, 20, 18)
        sync_layout.setSpacing(12)

        sync_title = QLabel("Synchronization")
        sync_title.setObjectName("SectionTitle")

        outlook_check = QCheckBox("Enable Outlook synchronization")
        outlook_check.setChecked(True)

        auto_sync = QCheckBox("Synchronize automatically")
        auto_sync.setChecked(True)

        sync_layout.addWidget(sync_title)
        sync_layout.addWidget(outlook_check)
        sync_layout.addWidget(auto_sync)

        root.addWidget(sync)

        actions = QHBoxLayout()
        actions.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setObjectName("Secondary")
        cancel.setCursor(Qt.PointingHandCursor)

        save = QPushButton("Save settings")
        save.setObjectName("Primary")
        save.setCursor(Qt.PointingHandCursor)

        actions.addWidget(cancel)
        actions.addWidget(save)

        root.addLayout(actions)
        root.addStretch()

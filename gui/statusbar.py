from PySide6.QtWidgets import QStatusBar, QLabel


class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()

        self.setObjectName("StatusBar")

        self.lbl_status = QLabel("Ready")
        self.lbl_db = QLabel("Database: Online")
        self.lbl_version = QLabel("v1.0")

        self.addWidget(self.lbl_status)
        self.addPermanentWidget(self.lbl_db)
        self.addPermanentWidget(self.lbl_version)

    def set_status(self, text):
        self.lbl_status.setText(text)

    def set_database(self, online=True):
        self.lbl_db.setText(
            "Database: Online" if online else "Database: Offline"
        )

    def set_version(self, version):
        self.lbl_version.setText(version)

from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFrame,QLabel,QGridLayout
from modules.database import Database

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db=Database()
        self.setStyleSheet("""
QFrame#Card,QFrame#Panel{background:white;border:1px solid #dde3ea;border-radius:12px;}
QLabel#Value{font:700 24px 'Segoe UI';color:#1f2937;}
QLabel#Caption{font:10pt 'Segoe UI';color:#6b7280;}
QLabel#PanelTitle{font:700 11pt 'Segoe UI';color:#374151;}
""")
        root=QVBoxLayout(self)
        root.setContentsMargins(18,18,18,18)
        root.setSpacing(16)
        cards=QHBoxLayout()
        cards.setSpacing(14)
        cards.addWidget(self.card("Emails",str(self.db.total_emails())))
        cards.addWidget(self.card("Companies",str(self.db.total_domains())))
        cards.addWidget(self.card("Last contact",str(self.db.last_email())[:10]))
        cards.addWidget(self.card("Status","READY"))
        root.addLayout(cards)
        grid=QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.addWidget(self.panel("Recent emails"),0,0)
        grid.addWidget(self.panel("Latest companies"),0,1)
        grid.addWidget(self.panel("Activity"),1,0,1,2)
        root.addLayout(grid)
    def card(self,title,value):
        f=QFrame(objectName="Card")
        l=QVBoxLayout(f)
        l.addWidget(QLabel(title,objectName="Caption"))
        l.addStretch()
        l.addWidget(QLabel(value,objectName="Value"))
        return f
    def panel(self,title):
        f=QFrame(objectName="Panel")
        l=QVBoxLayout(f)
        l.addWidget(QLabel(title,objectName="PanelTitle"))
        l.addStretch()
        return f

PRIMARY = "#00A3E0"
SIDEBAR = "#1F2D3D"
BACKGROUND = "#F4F6F9"
CARD = "#FFFFFF"
BORDER = "#D9E1E7"
TEXT = "#263238"
MUTED = "#6B7280"


def app_styles():
    return """
QMainWindow {
    background:%s;
}

QWidget {
    background:%s;
    font-family:'Segoe UI';
    font-size:10pt;
    color:%s;
}

QFrame#Sidebar {
    background:%s;
    border:none;
}

QLabel#LogoTitle {
    color:white;
    font-size:22px;
    font-weight:700;
}

QLabel#LogoSubtitle {
    color:#D8E4EC;
    font-size:10pt;
}

QPushButton {
    border:none;
    border-radius:8px;
    padding:10px 14px;
}

QPushButton#MenuButton {
    background:transparent;
    color:white;
    text-align:left;
    font-size:10.5pt;
}

QPushButton#MenuButton:hover {
    background:#2B3E52;
}

QPushButton#MenuButton:checked {
    background:%s;
    font-weight:700;
}

QFrame#TopBar,
QFrame#Card,
QFrame#Panel,
QStatusBar {
    background:white;
    border:1px solid %s;
    border-radius:10px;
}

QLabel#PageTitle {
    font-size:20px;
    font-weight:700;
}

QLabel#Secondary {
    color:%s;
}
""" % (BACKGROUND,BACKGROUND,TEXT,SIDEBAR,PRIMARY,BORDER,MUTED)

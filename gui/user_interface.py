import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

VALID_USERS = {
    "alice": "secret123",
    "bob": "hunter2",
}

# === Konfiguration ===
LOGO_PATH = "../images/Aurelic Logo mit Clar Leitmotiv.png"
FIELD_HEIGHT = 44  # Höhe der Eingabefelder/Buttons; Logo = 2x hiervon
PANEL_WIDTH = 360  # Breite des zentrierten Panels (Logo und Felder)

# Stylesheet mit deinem Color-Scheme
DARK_STYLE = """
/* Basis */
QWidget {
    background-color: #0D0D0D;   /* Near-Black Hintergrund */
    color: #F2EFEA;              /* Off-White Text */
    font-size: 14px;
}

/* Titel */
QLabel#title {
    color: #DFE5F3;              /* hellblau für Headlines */
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
}

/* Logo-Container: gleiches Look&Feel wie Felder, doppelte Höhe im Code */
QLabel#logo {
    /* Höhe kommt aus Python (4 * FIELD_HEIGHT) */
}

/* Eingabefelder (NICHT grün innen) */
QLineEdit {
    background-color: #0D0D0D;   /* Innen: near-black */
    color: #F2EFEA;              /* Text in Inputs */
    border: 1px solid #557373;   /* türkis-grauer Akzent */
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #B0B0B0;  /* Markierung */
    selection-color: #0D0D0D;
}
QLineEdit:focus {
    border-color: #DFE5F3;       /* Fokus-Highlight */
}
QLineEdit::placeholder {
    color: #557373;              /* dezenter Placeholder */
}

/* Buttons */
QPushButton {
    background-color: #557373;   /* Akzentfläche */
    color: #F2EFEA;
    font-weight: 600;
    border: 1px solid #557373;
    border-radius: 8px;
    padding: 8px 10px;
}
QPushButton:hover {
    border-color: #DFE5F3;
}
QPushButton:pressed {
    background-color: #272401;   /* dunkles Oliv als Press-State */
    border-color: #DFE5F3;
}

/* Dialoge */
QMessageBox { background-color: #0D0D0D; }
QMessageBox QLabel { color: #F2EFEA; }
"""

class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        # --- Inhalt ins Panel (wird zentriert) ---
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(12)

        # Logo (oben, exakt Panel-Breite, doppelte Feldhöhe)
        self.logo = QLabel()
        self.logo.setObjectName("logo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedHeight(FIELD_HEIGHT * 2)
        # Bild laden oder Platzhalter
        if LOGO_PATH:
            pm = QPixmap(LOGO_PATH)
            if not pm.isNull():
                # Füllt den verfügbaren Raum exakt (wie gewünscht)
                # Hinweis: setScaledContents skaliert proportional nicht zwingend;
                # für exakte Maße ist das ok. Bei Verzerrung -> pm.scaled(...) in resizeEvent.
                self.logo.setScaledContents(True)
                self.logo.setPixmap(pm)
            else:
                self.logo.setText("Logo")
        else:
            self.logo.setText("Logo")

        title = QLabel("Bitte anmelden")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("E-Mail-Adresse oder Benutzername")
        self.user_edit.setClearButtonEnabled(True)
        self.user_edit.setFixedHeight(FIELD_HEIGHT)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Passwort")
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setClearButtonEnabled(True)
        self.pass_edit.setFixedHeight(FIELD_HEIGHT)

        self.login_btn = QPushButton("Anmelden")
        self.login_btn.setToolTip("Mit Enter oder Alt+A anmelden")
        self.login_btn.setShortcut("Alt+A")
        self.login_btn.clicked.connect(self.try_login)
        self.login_btn.setFixedHeight(FIELD_HEIGHT)

        # Enter/Return löst Login aus
        self.user_edit.returnPressed.connect(self.try_login)
        self.pass_edit.returnPressed.connect(self.try_login)

        panel_layout.addWidget(self.logo)
        panel_layout.addWidget(title)
        panel_layout.addWidget(self.user_edit)
        panel_layout.addWidget(self.pass_edit)
        panel_layout.addWidget(self.login_btn)

        # Fixe Panel-Breite für schönes, zentriertes Layout
        panel.setFixedWidth(PANEL_WIDTH)

        # --- Außenlayout: zentriert das Panel im Fenster (horizontal & vertikal) ---
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(panel, alignment=Qt.AlignmentFlag.AlignCenter)

        self.user_edit.setFocus()

    def try_login(self):
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()
        if VALID_USERS.get(username) == password:
            self.on_login_success(username)
            self.pass_edit.clear()
        else:
            QMessageBox.warning(self, "Fehler", "Benutzername oder Passwort falsch.")
            self.pass_edit.selectAll()
            self.pass_edit.setFocus()

class HomePage(QWidget):
    def __init__(self, username, on_logout):
        super().__init__()
        self.on_logout = on_logout

        # --- Inhalt ins Panel (wird zentriert) ---
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(12)

        hello = QLabel(f"Willkommen, {username}!")
        hello.setObjectName("title")
        hello.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        logout_btn = QPushButton("Abmelden")
        logout_btn.clicked.connect(self.on_logout)
        logout_btn.setFixedHeight(FIELD_HEIGHT)

        panel_layout.addWidget(hello)
        panel_layout.addWidget(logout_btn)

        panel.setFixedWidth(PANEL_WIDTH)

        # --- Außenlayout: zentriert das Panel ---
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(panel, alignment=Qt.AlignmentFlag.AlignCenter)

class App(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DARK_STYLE)   # global anwenden
        self.login_page = LoginPage(self.login_success)
        self.addWidget(self.login_page)

    def login_success(self, username):
        # vorhandene HomePage (falls vorhanden) entfernen
        if self.count() > 1:
            old = self.widget(1)
            self.removeWidget(old)
            old.deleteLater()
        self.home_page = HomePage(username, self.logout)
        self.addWidget(self.home_page)
        self.setCurrentIndex(1)

    def logout(self):
        self.setCurrentIndex(0)

def main_window():
    app = QApplication(sys.argv)
    w = App()
    w.setWindowTitle("Login Demo")
    w.resize(500, 420)  # etwas höher: wegen Logo
    w.show()
    sys.exit(app.exec())
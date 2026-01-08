import os
import sys
from dotenv import load_dotenv
load_dotenv()
from gui.benutzerpage_settings import UserPage

# Windows: sorgt dafür, dass die Taskleiste nicht das python.exe-Icon (Rakete) nimmt
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("aurelic.stockapp")

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStackedWidget, QMessageBox

# --- FINNHUB API KEY: aus System-Env lesen (empfohlen) ---
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_KEY:
    raise RuntimeError(
        "FINNHUB_API_KEY is not set. "
        "Please set it as an environment variable before starting the app."
    )

from gui.startpage import StartPage
from gui.mainpage import MainPage
from gui.analysepage import AnalysePage
from data.db_connection import get_connection
from controller.auth import AuthController


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ===== APP / FENSTER ICON =====
    # Absoluter Pfad ist stabiler (IDE/Working-Dir)
    icon_path = os.path.abspath("images/content.png")  # oder "images/app_icon.png"
    icon = QIcon(icon_path)

    # Optionales Debug (wenn Icon nicht greift)
    # print("Icon path:", icon_path)
    # print("Icon isNull:", icon.isNull())

    app.setWindowIcon(icon)

    db_conn = get_connection()
    auth_ctrl = AuthController(db_conn)

    stack = QStackedWidget()
    stack.setWindowTitle("Aurelic")

    # Top-Level-Fenster explizit setzen (empfohlen)
    stack.setWindowIcon(icon)

    start = StartPage(logo_path="images/Aurelic Logo mit Clar Leitmotiv.png")

    # Pages müssen existieren, bevor Lambda sie referenziert
    main = MainPage()
    analyse = AnalysePage()
    user_page = UserPage()

    # Login/Register wiring
    start.login_requested.connect(auth_ctrl.on_login)
    auth_ctrl.login_successful.connect(lambda: stack.setCurrentWidget(main))
    auth_ctrl.login_failed.connect(lambda msg: QMessageBox.warning(start, "Login failed", msg))

    start.register_requested_v2.connect(auth_ctrl.on_register)
    auth_ctrl.register_successful.connect(lambda: stack.setCurrentWidget(main))
    auth_ctrl.register_failed.connect(lambda msg: QMessageBox.warning(start, "Register failed", msg))

    stack.addWidget(start)    # index 0
    stack.addWidget(main)     # index 1
    stack.addWidget(analyse)  # index 2
    stack.addWidget(user_page)  # index 3

    # Startseite
    stack.setCurrentWidget(start)

    def on_tab(which: str):
        if which == "brokerage":
            stack.setCurrentWidget(main)
        elif which == "analyse":
            stack.setCurrentWidget(analyse)

    main.tab_changed.connect(on_tab)
    analyse.tab_changed.connect(on_tab)

    # --- Avatar ("N") -> UserPage, und Zurück zur vorherigen Seite ---
    _last_page = {"w": main}  # mutable container


    def goto(widget):
        _last_page["w"] = stack.currentWidget()
        stack.setCurrentWidget(widget)


    main.avatar_clicked.connect(lambda: goto(user_page))
    analyse.avatar_clicked.connect(lambda: goto(user_page))  # falls AnalysePage auch ein Avatar hat

    user_page.back_requested.connect(lambda: stack.setCurrentWidget(_last_page["w"]))


    def on_key(event):
        if event.key() == Qt.Key_F1:
            stack.setCurrentWidget(start); return
        if event.key() == Qt.Key_F2:
            stack.setCurrentWidget(main); return
        if event.key() == Qt.Key_F3:
            stack.setCurrentWidget(analyse); return
        if event.key() == Qt.Key_Escape:
            app.quit(); return
        QStackedWidget.keyPressEvent(stack, event)

    stack.keyPressEvent = on_key
    stack.showMaximized()
    sys.exit(app.exec())

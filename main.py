import os
import sys
from dotenv import load_dotenv
load_dotenv()

from PySide6.QtCore import Qt
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

    db_conn = get_connection()
    auth_ctrl = AuthController(db_conn)

    stack = QStackedWidget()

    start = StartPage(logo_path="images/Aurelic Logo mit Clar Leitmotiv.png")

    # Pages müssen existieren, bevor Lambda sie referenziert
    main = MainPage()
    analyse = AnalysePage()

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

    # Startseite: sinnvollerweise Start/Login (nicht Brokerage)
    stack.setCurrentWidget(start)

    def on_tab(which: str):
        if which == "brokerage":
            stack.setCurrentWidget(main)
        elif which == "analyse":
            stack.setCurrentWidget(analyse)

    main.tab_changed.connect(on_tab)
    analyse.tab_changed.connect(on_tab)

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

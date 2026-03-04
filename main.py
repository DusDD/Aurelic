# main.py (final: Avatar dynamisch + Passwort-Flow robust + Favorites (Top 6) verdrahtet
#          + Favorites -> MainPage wiring + Auto-Refresh nach Add/Remove + Initial Sync
#          + Investments-Page (investment.py) in Stack + Navigation über MainPage.investments_clicked)

import os
import sys
from typing import Optional

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

from gui.startpage import StartPage
from gui.mainpage import MainPage, Palette
from gui.analysepage import AnalysePage
from gui.calendarpage import CalendarPage

# ✅ NEW: Investment Page + Controller
from gui.investment import InvestmentPage
from controller.investments import InvestmentsController

from data.db_connection import get_connection
from controller.auth import AuthController

# Favorites Controller
from controller.favorites import FavoritesController


# --- FINNHUB API KEY: aus System-Env lesen (empfohlen) ---
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_KEY:
    raise RuntimeError(
        "FINNHUB_API_KEY is not set. "
        "Please set it as an environment variable before starting the app."
    )

# --- FMP API KEY: aus System-Env lesen (empfohlen) ---
FMP_KEY = os.getenv("FMP_API_KEY")
if not FMP_KEY:
    raise RuntimeError(
        "FMP_API_KEY is not set. "
        "Please set it as an environment variable before starting the app."
    )


def _favorites_to_symbols(items: Optional[list[dict]]) -> list[str]:
    """Normalisiert favorites_loaded(list[dict]) -> list[str] symbols (max 6)."""
    out: list[str] = []
    seen = set()
    for it in (items or []):
        if not isinstance(it, dict):
            continue
        sym = (it.get("symbol") or "").strip().upper()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        out.append(sym)
    return out[:6]


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ===== APP / FENSTER ICON =====
    icon_path = os.path.abspath("images/content.png")
    icon = QIcon(icon_path)
    app.setWindowIcon(icon)

    # ===== DB / CONTROLLER =====
    db_conn = get_connection()
    auth_ctrl = AuthController(db_conn)

    # Favorites Controller (Top 6, ohne Reihenfolge)
    favorites_ctrl = FavoritesController(db_conn, auth_ctrl)

    # ✅ NEW: Investments Controller
    investments_ctrl = InvestmentsController(db_conn, auth_ctrl)

    # ===== STACK =====
    stack = QStackedWidget()
    stack.setWindowTitle("Aurelic")
    stack.setWindowIcon(icon)

    # ===== PAGES =====
    start = StartPage(logo_path="images/Aurelic Logo mit Clar Leitmotiv.png")
    main = MainPage()
    analyse = AnalysePage()
    user_page = UserPage()

    palette = Palette()
    calendar = CalendarPage(palette=palette, background_path="images/Backgroundimage.png")

    # ✅ NEW: Investment Page (DB-basiert)
    investment_page = InvestmentPage(
        investments_ctrl=investments_ctrl,
        background_path="images/Backgroundimage.png"
    )

    # ===== STACK ADD =====
    stack.addWidget(start)            # index 0
    stack.addWidget(main)             # index 1
    stack.addWidget(analyse)          # index 2
    stack.addWidget(user_page)        # index 3
    stack.addWidget(calendar)         # index 4
    stack.addWidget(investment_page)  # index 5 ✅ NEW

    stack.setCurrentWidget(start)

    # -----------------------------
    # Helper: User laden + Avatar-Buchstabe setzen
    # -----------------------------
    def apply_user_to_ui() -> dict | None:
        """
        Lädt den aktuellen User (falls eingeloggt) und setzt Avatar-Buchstaben in allen Pages,
        die set_avatar_from_user(user) implementieren.
        Gibt den user dict zurück (oder None).
        """
        try:
            user = auth_ctrl.get_current_user()
        except Exception:
            user = None

        for page in (main, analyse, user_page, investment_page):
            if hasattr(page, "set_avatar_from_user"):
                try:
                    page.set_avatar_from_user(user)
                except Exception:
                    pass

        # Wenn kein User: Favoriten im Main leeren
        if user is None and hasattr(main, "set_favorite_symbols"):
            try:
                main.set_favorite_symbols([])
            except Exception:
                pass

        # ✅ Optional: Analyse auch leeren, wenn kein User
        if user is None and hasattr(analyse, "set_favorite_symbols"):
            try:
                analyse.set_favorite_symbols([])
            except Exception:
                pass

        return user

    # -----------------------------
    # Favorites wiring (Top 6)
    # -----------------------------
    def _wire_favorites_ui():
        # Controller -> UI (UserPage + MainPage + AnalysePage) aus EINEM Event
        def _on_favorites_loaded(items: list[dict] | None):
            # UserPage füttern
            if hasattr(user_page, "set_favorites"):
                try:
                    user_page.set_favorites(items)
                except Exception:
                    pass

            symbols = _favorites_to_symbols(items)

            # MainPage füttern (nur Symbole)
            if hasattr(main, "set_favorite_symbols"):
                try:
                    main.set_favorite_symbols(symbols)
                except Exception:
                    pass

            # ✅ AnalysePage füttern (Quantitative Analyse)
            if hasattr(analyse, "set_favorite_symbols"):
                try:
                    analyse.set_favorite_symbols(symbols)
                except Exception:
                    pass

        # Wenn Controller ein Signal favorites_loaded hat
        if hasattr(favorites_ctrl, "favorites_loaded"):
            try:
                favorites_ctrl.favorites_loaded.connect(_on_favorites_loaded)
            except Exception:
                pass

        # Fehler
        if hasattr(favorites_ctrl, "favorites_failed"):
            try:
                favorites_ctrl.favorites_failed.connect(
                    lambda msg: QMessageBox.warning(user_page, "Favoriten", msg)
                )
            except Exception:
                pass

        # UI -> Controller: Refresh
        if hasattr(user_page, "favorites_refresh_requested") and hasattr(favorites_ctrl, "load_favorites"):
            try:
                user_page.favorites_refresh_requested.connect(favorites_ctrl.load_favorites)
            except Exception:
                pass

        # UI -> Controller: Add (mit Auto-Refresh)
        if hasattr(user_page, "favorite_add_requested") and hasattr(favorites_ctrl, "add_favorite_symbol"):
            try:
                def _add_and_reload(symbol: str):
                    favorites_ctrl.add_favorite_symbol(symbol)
                    try:
                        favorites_ctrl.load_favorites()
                    except Exception:
                        pass

                user_page.favorite_add_requested.connect(_add_and_reload)
            except Exception:
                pass

        # UI -> Controller: Remove (mit Auto-Refresh)
        if hasattr(user_page, "favorite_remove_requested") and hasattr(favorites_ctrl, "remove_favorite"):
            try:
                def _remove_and_reload(asset_id: int):
                    favorites_ctrl.remove_favorite(asset_id)
                    try:
                        favorites_ctrl.load_favorites()
                    except Exception:
                        pass

                user_page.favorite_remove_requested.connect(_remove_and_reload)
            except Exception:
                pass

    _wire_favorites_ui()

    # -----------------------------
    # Navigation helper
    # -----------------------------
    _last_page = {"w": main}  # mutable container

    def goto(widget):
        _last_page["w"] = stack.currentWidget()

        # Wenn wir zur UserPage gehen -> Userdaten laden + Avatar setzen + Favorites laden
        if widget is user_page:
            try:
                user = apply_user_to_ui()
                user_page.load_user(user)

                try:
                    favorites_ctrl.load_favorites()
                except Exception:
                    pass

            except Exception as e:
                QMessageBox.warning(user_page, "Profil", f"Userdaten konnten nicht geladen werden:\n{e}")

        # ✅ Wenn wir zur InvestmentPage gehen -> immer neu laden (DB)
        if widget is investment_page:
            try:
                investment_page.reload()
            except Exception:
                pass

        stack.setCurrentWidget(widget)

    # -----------------------------
    # Login/Register wiring
    # -----------------------------
    start.login_requested.connect(auth_ctrl.on_login)

    def _on_login_ok(email: str):
        apply_user_to_ui()
        stack.setCurrentWidget(main)

        try:
            favorites_ctrl.load_favorites()
        except Exception:
            pass

    auth_ctrl.login_successful.connect(_on_login_ok)
    auth_ctrl.login_failed.connect(lambda msg: QMessageBox.warning(start, "Login failed", msg))

    start.register_requested_v2.connect(auth_ctrl.on_register)

    def _on_register_ok(_full_name: str):
        apply_user_to_ui()
        stack.setCurrentWidget(main)

        try:
            favorites_ctrl.load_favorites()
        except Exception:
            pass

    auth_ctrl.register_successful.connect(_on_register_ok)
    auth_ctrl.register_failed.connect(lambda msg: QMessageBox.warning(start, "Register failed", msg))

    # -----------------------------
    # Tabs
    # -----------------------------
    def on_tab(which: str):
        if which == "brokerage":
            stack.setCurrentWidget(main)
        elif which == "analyse":
            stack.setCurrentWidget(analyse)
            # ✅ ensure analysis gets fresh favorites (if not loaded yet)
            try:
                favorites_ctrl.load_favorites()
            except Exception:
                pass

    main.tab_changed.connect(on_tab)
    analyse.tab_changed.connect(on_tab)

    # -----------------------------
    # Avatar -> UserPage
    # -----------------------------
    main.avatar_clicked.connect(lambda: goto(user_page))
    analyse.avatar_clicked.connect(lambda: goto(user_page))
    if hasattr(user_page, "back_requested"):
        user_page.back_requested.connect(lambda: stack.setCurrentWidget(_last_page["w"]))

    # -----------------------------
    # ✅ Investments Button -> InvestmentPage
    # (MainPage muss Signal investments_clicked haben)
    # -----------------------------
    if hasattr(main, "investments_clicked"):
        main.investments_clicked.connect(lambda: goto(investment_page))

    # InvestmentPage Back -> zurück zur letzten Seite
    if hasattr(investment_page, "back_clicked"):
        investment_page.back_clicked.connect(lambda: stack.setCurrentWidget(_last_page["w"]))

    # -----------------------------
    # Passwort ändern: zuverlässiger Flow
    # -----------------------------
    def on_password_change_request(current_pw: str, new_pw: str, new_pw2: str):
        if hasattr(user_page, "password_change_ui_busy"):
            try:
                user_page.password_change_ui_busy()
            except Exception:
                pass

        if hasattr(auth_ctrl, "change_password"):
            auth_ctrl.change_password(current_pw, new_pw, new_pw2)
        else:
            if hasattr(user_page, "password_change_ui_done"):
                try:
                    user_page.password_change_ui_done()
                except Exception:
                    pass
            QMessageBox.warning(user_page, "Passwort", "AuthController.change_password() fehlt noch.")

    user_page.password_change_requested.connect(on_password_change_request)

    def on_password_change_ok():
        if hasattr(user_page, "password_change_success"):
            try:
                user_page.password_change_success()
            except Exception:
                pass
        else:
            if hasattr(user_page, "password_change_ui_done"):
                try:
                    user_page.password_change_ui_done()
                except Exception:
                    pass
            if hasattr(user_page, "current_pw"):
                user_page.current_pw.clear()
            if hasattr(user_page, "new_pw"):
                user_page.new_pw.clear()
            if hasattr(user_page, "new_pw2"):
                user_page.new_pw2.clear()

        QMessageBox.information(user_page, "Passwort geändert", "Dein Passwort wurde erfolgreich aktualisiert.")

    def on_password_change_fail(msg: str):
        if hasattr(user_page, "password_change_ui_done"):
            try:
                user_page.password_change_ui_done()
            except Exception:
                pass
        QMessageBox.warning(user_page, "Passwort ändern fehlgeschlagen", msg)

    if hasattr(auth_ctrl, "password_change_successful"):
        auth_ctrl.password_change_successful.connect(on_password_change_ok)
    if hasattr(auth_ctrl, "password_change_failed"):
        auth_ctrl.password_change_failed.connect(on_password_change_fail)

    # -----------------------------
    # Kalender -> CalendarPage
    # -----------------------------
    main.calendar_clicked.connect(lambda: goto(calendar))
    analyse.calendar_clicked.connect(lambda: goto(calendar))
    if hasattr(calendar, "back_clicked"):
        calendar.back_clicked.connect(lambda: stack.setCurrentWidget(_last_page["w"]))

    # -----------------------------
    # Hotkeys
    # -----------------------------
    def on_key(event):
        if event.key() == Qt.Key_F1:
            stack.setCurrentWidget(start)
            return
        if event.key() == Qt.Key_F2:
            stack.setCurrentWidget(main)
            return
        if event.key() == Qt.Key_F3:
            stack.setCurrentWidget(analyse)
            return
        if event.key() == Qt.Key_F4:
            stack.setCurrentWidget(investment_page)  # ✅ NEW
            return
        if event.key() == Qt.Key_Escape:
            app.quit()
            return
        QStackedWidget.keyPressEvent(stack, event)

    stack.keyPressEvent = on_key

    # -----------------------------
    # Initial: UI vorbereiten (Avatar, ggf. Favoriten leeren)
    # -----------------------------
    apply_user_to_ui()

    stack.showMaximized()
    sys.exit(app.exec())
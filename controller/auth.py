from PySide6.QtCore import QObject, Signal, QTimer
from src.auth.register import register_user
from src.auth.login import login_user
from src.auth.security import check_rate_limit
from src.auth.token import blacklist_token

class AuthController(QObject):
    login_successful = Signal(str)          # email
    login_failed = Signal(str)              # error message
    register_successful = Signal(str)       # full name
    register_failed = Signal(str)           # error message
    password_reset_sent = Signal(str)       # email
    password_reset_failed = Signal(str)     # error message
    password_reset_done = Signal(str)       # email

    def __init__(self, db_conn, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.current_token = None

    # -----------------------------
    # LOGIN
    # -----------------------------
    def on_login(self, email: str, password: str):

        if not check_rate_limit(email):
            self.login_failed.emit("Too many login attempts.")
            return

        result = login_user(email, password)

        if result.get("success"):
            self.current_token = result["token"]
            self.login_successful.emit(email)
        else:
            self.login_failed.emit(result.get("error"))

        if result.get("success"):
            self.login_successful.emit(email)
        else:
            self.login_failed.emit(result.get("error", "Login failed"))

    # -----------------------------
    # REGISTER
    # -----------------------------
    def on_register(
            self,
            first_name,
            last_name,
            email,
            pw1,
            pw2,
            street="",
            postal_code="",
            city="",
            country=""
    ):
        # Passwort-Match prüfen
        if pw1 != pw2:
            self.register_failed.emit("passwords_do_not_match")
            return

        result = register_user(
            first_name, last_name, email, pw1,
            street=street,
            postal=postal_code,
            city=city,
            country=country
        )

        if result.get("success"):
            full_name = f"{first_name} {last_name}".strip()
            self.register_successful.emit(full_name)
        else:
            self.register_failed.emit(result.get("error", "Registration failed"))

    # -----------------------------
    # PASSWORD RESET
    # -----------------------------
    def send_reset_code(self, email: str):
        # This function should trigger sending a code via email
        # Currently, we just simulate success
        if not email or "@" not in email:
            self.password_reset_failed.emit("Invalid email")
            return

        # In real implementation, generate code + store in DB
        self.password_reset_sent.emit(email)

    def reset_password(self, email: str, code: str, new_password: str):
        # Verify code in DB, then update password
        if not code or len(code) != 6:
            self.password_reset_failed.emit("Invalid code")
            return

        result = login_user(email, new_password, reset=True)
        if result.get("success"):
            self.password_reset_done.emit(email)
        else:
            self.password_reset_failed.emit(result.get("error", "Password reset failed"))

    def logout(self):
        if self.current_token:
            blacklist_token(self.current_token)
            self.current_token = None

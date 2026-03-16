from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.auth.register import register_user
from src.auth.login import login_user
from src.auth.security import check_rate_limit
from src.auth.token import blacklist_token


class AuthController(QObject):
    # Signals
    login_successful = Signal(str)          # email
    login_failed = Signal(str)              # error message

    register_successful = Signal(str)       # full name
    register_failed = Signal(str)           # error message

    password_reset_sent = Signal(str)       # email
    password_reset_failed = Signal(str)     # error message
    password_reset_done = Signal(str)       # email

    # NEW: Passwort ändern
    password_change_successful = Signal()
    password_change_failed = Signal(str)

    def __init__(self, db_conn, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.current_token: str | None = None
        self.current_email: str | None = None  # merkt sich den eingeloggten User (email)

    # -----------------------------
    # USER LOAD (für UserPage)
    # -----------------------------
    def get_user_by_email(self, email: str) -> dict | None:
        if not email:
            return None

        sql = """
            SELECT
                id,
                email,
                first_name,
                last_name,
                street,
                postal_code,
                city,
                country
            FROM auth.users
            WHERE lower(email) = lower(%s)
              AND deleted_at IS NULL
            LIMIT 1
        """

        try:
            with self.db_conn.cursor() as cur:
                cur.execute(sql, (email,))
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    "id": row[0],
                    "email": row[1],
                    "first_name": row[2],
                    "last_name": row[3],
                    "street": row[4],
                    "postal_code": row[5],
                    "city": row[6],
                    "country": row[7],
                }
        except Exception:
            return None

    def get_current_user(self) -> dict | None:
        if not self.current_email:
            return None
        return self.get_user_by_email(self.current_email)

    # -----------------------------
    # LOGIN
    # -----------------------------
    def on_login(self, email: str, password: str) -> None:
        if not check_rate_limit(email):
            self.login_failed.emit("Too many login attempts.")
            return

        result = login_user(email, password)

        if result.get("success"):
            self.current_token = result.get("token")
            self.current_email = email
            self.login_successful.emit(email)
        else:
            self.login_failed.emit(result.get("error", "Login failed"))

    # -----------------------------
    # REGISTER
    # -----------------------------
    def on_register(
        self,
        first_name: str,
        last_name: str,
        email: str,
        pw1: str,
        pw2: str,
        street: str = "",
        postal_code: str = "",
        city: str = "",
        country: str = "",
    ) -> None:
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
    # PASSWORD RESET (Prototype)
    # -----------------------------
    def send_reset_code(self, email: str) -> None:
        if not email or "@" not in email:
            self.password_reset_failed.emit("Invalid email")
            return
        self.password_reset_sent.emit(email)

    def reset_password(self, email: str, code: str, new_password: str) -> None:
        if not code or len(code) != 6:
            self.password_reset_failed.emit("Invalid code")
            return

        result = login_user(email, new_password, reset=True)
        if result.get("success"):
            self.password_reset_done.emit(email)
        else:
            self.password_reset_failed.emit(result.get("error", "Password reset failed"))

    # -----------------------------
    # PASSWORD CHANGE (Echt)
    # -----------------------------
    def change_password(self, current_pw: str, new_pw: str, new_pw2: str) -> None:
        """
        Ändert das Passwort für den aktuell eingeloggten User.
        Erwartet: self.current_email ist gesetzt (nach Login).
        """
        try:
            if not self.current_email:
                self.password_change_failed.emit("Nicht eingeloggt.")
                return

            if not current_pw or not new_pw or not new_pw2:
                self.password_change_failed.emit("Bitte alle Passwortfelder ausfüllen.")
                return

            if new_pw != new_pw2:
                self.password_change_failed.emit("Die neuen Passwörter stimmen nicht überein.")
                return

            if len(new_pw) < 8:
                self.password_change_failed.emit("Neues Passwort muss mindestens 8 Zeichen lang sein.")
                return

            # 1) user + hash laden
            with self.db_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, password_hash
                    FROM auth.users
                    WHERE lower(email) = lower(%s)
                      AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    (self.current_email,),
                )
                row = cur.fetchone()

            if not row:
                self.password_change_failed.emit("User nicht gefunden.")
                return

            user_id, stored_hash = row[0], row[1]
            if not stored_hash:
                self.password_change_failed.emit("Kein Passwort-Hash gefunden.")
                return

            stored_hash_str = str(stored_hash)

            # 2) Passwort verifizieren + neuen Hash erzeugen (auto-detect)
            # --- bcrypt ---
            if stored_hash_str.startswith("$2a$") or stored_hash_str.startswith("$2b$") or stored_hash_str.startswith("$2y$"):
                try:
                    import bcrypt
                except ImportError:
                    self.password_change_failed.emit("bcrypt fehlt (pip install bcrypt).")
                    return

                ok = bcrypt.checkpw(current_pw.encode("utf-8"), stored_hash_str.encode("utf-8"))
                if not ok:
                    self.password_change_failed.emit("Aktuelles Passwort ist falsch.")
                    return

                new_hash = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # --- passlib pbkdf2_sha256 ---
            elif stored_hash_str.startswith("$pbkdf2-sha256$") or "pbkdf2_sha256" in stored_hash_str:
                try:
                    from passlib.hash import pbkdf2_sha256
                except ImportError:
                    self.password_change_failed.emit("passlib fehlt (pip install passlib).")
                    return

                ok = pbkdf2_sha256.verify(current_pw, stored_hash_str)
                if not ok:
                    self.password_change_failed.emit("Aktuelles Passwort ist falsch.")
                    return

                new_hash = pbkdf2_sha256.hash(new_pw)

            else:
                self.password_change_failed.emit(
                    "Unbekanntes Hash-Format. Sag mir, wie ihr hasht (bcrypt/pbkdf2/sha256?), dann passe ich es an."
                )
                return

            # 3) DB Update + commit
            with self.db_conn.cursor() as cur:
                cur.execute(
                    "UPDATE auth.users SET password_hash = %s WHERE id = %s",
                    (new_hash, user_id),
                )
            self.db_conn.commit()

            self.password_change_successful.emit()

        except Exception as e:
            try:
                self.db_conn.rollback()
            except Exception:
                pass
            self.password_change_failed.emit(f"Fehler beim Passwortwechsel: {e}")

    # -----------------------------
    # LOGOUT
    # -----------------------------
    def logout(self) -> None:
        if self.current_token:
            blacklist_token(self.current_token)

        self.current_token = None
        self.current_email = None
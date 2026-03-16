# controller/favorites.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal, Slot


class FavoritesController(QObject):
    """
    Controller für 'Top 6 Favoriten' (ohne Reihenfolge).
    Erwartet:
      - db_conn: psycopg2 Connection (oder kompatibel)
      - auth_ctrl: Objekt mit get_current_user() -> dict (mindestens {"id": ...})
    """

    favorites_loaded = Signal(list)   # list[dict]: [{"asset_id": int, "symbol": str, "name": str}]
    favorites_failed = Signal(str)

    favorite_added = Signal(str)      # symbol
    favorite_removed = Signal(int)    # asset_id

    def __init__(self, db_conn, auth_ctrl, parent: QObject | None = None):
        super().__init__(parent)
        self._db = db_conn
        self._auth = auth_ctrl

    # --------------------------
    # Internals
    # --------------------------
    def _current_user_id(self) -> int:
        user = None
        try:
            user = self._auth.get_current_user()
        except Exception:
            user = None

        if not user or "id" not in user or user["id"] is None:
            raise RuntimeError("Kein eingeloggter User (user.id fehlt).")
        return int(user["id"])

    def _fetch_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        # stocks.assets hat canonical_symbol, nicht symbol
        sql = """
            SELECT
                a.asset_id,
                a.canonical_symbol AS symbol,
                COALESCE(a.name, a.canonical_symbol) AS name
            FROM stocks.favorites f
            JOIN stocks.assets a ON a.asset_id = f.asset_id
            WHERE f.user_id = %s
            ORDER BY a.canonical_symbol ASC
            LIMIT 6
        """
        with self._db.cursor() as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "asset_id": int(r[0]),
                    "symbol": str(r[1] or "").strip(),
                    "name": str(r[2] or "").strip(),
                }
            )
        return out

    def _resolve_asset_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        sym = (symbol or "").strip().upper()
        if not sym:
            return None

        # canonical_symbol ist das "Symbol" in stocks.assets
        sql = """
            SELECT
                asset_id,
                canonical_symbol AS symbol,
                COALESCE(name, canonical_symbol) AS name
            FROM stocks.assets
            WHERE UPPER(canonical_symbol) = %s
            LIMIT 1
        """
        with self._db.cursor() as cur:
            cur.execute(sql, (sym,))
            row = cur.fetchone()

        if not row:
            return None

        return {
            "asset_id": int(row[0]),
            "symbol": str(row[1] or "").strip(),
            "name": str(row[2] or "").strip(),
        }

    def _favorites_count(self, user_id: int) -> int:
        sql = "SELECT COUNT(*) FROM stocks.favorites WHERE user_id = %s"
        with self._db.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
        return int(row[0] if row else 0)

    # --------------------------
    # Public API (Slots)
    # --------------------------
    @Slot()
    def load_favorites(self) -> None:
        """Lädt Favoriten (max 6) und emittiert favorites_loaded(list)."""
        try:
            uid = self._current_user_id()
            favs = self._fetch_favorites(uid)
            self.favorites_loaded.emit(favs)
        except Exception as e:
            self.favorites_failed.emit(str(e))

    @Slot(str)
    def add_favorite_symbol(self, symbol: str) -> None:
        """
        Fügt Favorit über Symbol hinzu:
          - Symbol -> asset_id
          - Limit 6 prüfen
          - INSERT ON CONFLICT DO NOTHING
          - danach Favoritenliste emittieren
        """
        try:
            uid = self._current_user_id()

            sym = (symbol or "").strip().upper()
            if not sym:
                raise RuntimeError("Bitte ein Symbol eingeben.")

            asset = self._resolve_asset_by_symbol(sym)
            if not asset:
                raise RuntimeError(f"Symbol nicht gefunden: {sym}")

            # Limit 6 (DB-seitig absichern)
            cnt = self._favorites_count(uid)
            if cnt >= 6:
                raise RuntimeError("Du hast bereits 6 Favoriten. Entferne erst einen Favoriten.")

            sql = """
                INSERT INTO stocks.favorites (user_id, asset_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, asset_id) DO NOTHING
            """
            with self._db.cursor() as cur:
                cur.execute(sql, (uid, asset["asset_id"]))
            self._db.commit()

            self.favorite_added.emit(asset["symbol"])

            favs = self._fetch_favorites(uid)
            self.favorites_loaded.emit(favs)

        except Exception as e:
            # rollback, falls DB in Transaktion ist
            try:
                self._db.rollback()
            except Exception:
                pass
            self.favorites_failed.emit(str(e))

    @Slot(int)
    def remove_favorite(self, asset_id: int) -> None:
        """
        Entfernt Favorit per asset_id.
        Danach Favoritenliste emittieren.
        """
        try:
            uid = self._current_user_id()
            aid = int(asset_id)

            sql = "DELETE FROM stocks.favorites WHERE user_id = %s AND asset_id = %s"
            with self._db.cursor() as cur:
                cur.execute(sql, (uid, aid))
            self._db.commit()

            self.favorite_removed.emit(aid)

            favs = self._fetch_favorites(uid)
            self.favorites_loaded.emit(favs)

        except Exception as e:
            try:
                self._db.rollback()
            except Exception:
                pass
            self.favorites_failed.emit(str(e))
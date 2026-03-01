# controller/investments.py
from __future__ import annotations

from typing import Optional

VALID_CATEGORIES = {"stock", "etf", "crypto", "commodity", "index"}


# Wichtig:
# - assets: nur "kanonische" Asset-Tabelle (symbol/name optional)
# - investments: user-spezifische Position inkl. category
UPSERT_ASSET_AND_INVESTMENT_SQL = """
WITH upsert_asset AS (
  INSERT INTO stocks.assets (canonical_symbol, name)
  VALUES (%s, %s)
  ON CONFLICT (canonical_symbol)
  DO UPDATE SET
    name = COALESCE(EXCLUDED.name, stocks.assets.name)
  RETURNING asset_id
),
resolved_asset AS (
  SELECT asset_id FROM upsert_asset
  UNION ALL
  SELECT asset_id FROM stocks.assets WHERE canonical_symbol = %s
  LIMIT 1
)
INSERT INTO stocks.investments (user_id, asset_id, quantity, category)
SELECT %s, asset_id, %s, %s
FROM resolved_asset
ON CONFLICT (user_id, asset_id)
DO UPDATE SET
  quantity = EXCLUDED.quantity,
  category = EXCLUDED.category
RETURNING user_id, asset_id, quantity, category;
"""


LIST_USER_INVESTMENTS_SQL = """
SELECT
  a.asset_id,
  a.canonical_symbol,
  a.name,
  i.category,
  i.quantity,
  i.updated_at
FROM stocks.investments i
JOIN stocks.assets a ON a.asset_id = i.asset_id
WHERE i.user_id = %s
ORDER BY a.canonical_symbol;
"""


DELETE_USER_INVESTMENT_BY_SYMBOL_SQL = """
DELETE FROM stocks.investments i
USING stocks.assets a
WHERE i.asset_id = a.asset_id
  AND i.user_id = %s
  AND a.canonical_symbol = %s;
"""


class InvestmentsController:
    def __init__(self, db_conn, auth_ctrl):
        self._conn = db_conn
        self._auth = auth_ctrl

    def _require_user_id(self, user_id: Optional[int]) -> int:
        if user_id is not None:
            return int(user_id)

        user = self._auth.get_current_user()
        if not user:
            raise RuntimeError("Nicht eingeloggt.")
        return int(user["id"])

    def upsert_user_investment(
        self,
        symbol: str,
        name: Optional[str],
        category: str,
        quantity: float,
        user_id: Optional[int] = None,
    ) -> dict:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("Symbol fehlt.")

        cat = (category or "").strip().lower()
        if cat not in VALID_CATEGORIES:
            raise ValueError(f"Ungültige Kategorie: {category}")

        q = float(quantity)
        if q < 0:
            raise ValueError("Quantity muss >= 0 sein.")

        uid = self._require_user_id(user_id)
        nm = (name or "").strip() or None

        with self._conn.cursor() as cur:
            cur.execute(
                UPSERT_ASSET_AND_INVESTMENT_SQL,
                (sym, nm, sym, uid, q, cat),
            )
            row = cur.fetchone()
            self._conn.commit()

        return {
            "user_id": int(row[0]),
            "asset_id": int(row[1]),
            "quantity": float(row[2]),
            "category": str(row[3]),
        }

    def list_user_investments(self, user_id: Optional[int] = None) -> list[dict]:
        uid = self._require_user_id(user_id)

        with self._conn.cursor() as cur:
            cur.execute(LIST_USER_INVESTMENTS_SQL, (uid,))
            rows = cur.fetchall()

        out: list[dict] = []
        for r in rows:
            out.append(
                {
                    "asset_id": int(r[0]),
                    "symbol": r[1],
                    "name": r[2],
                    "category": r[3],
                    "quantity": float(r[4]),
                    "updated_at": r[5],
                }
            )
        return out

    def delete_user_investment(self, symbol: str, user_id: Optional[int] = None) -> None:
        sym = (symbol or "").strip().upper()
        if not sym:
            raise ValueError("Symbol fehlt.")
        uid = self._require_user_id(user_id)

        with self._conn.cursor() as cur:
            cur.execute(DELETE_USER_INVESTMENT_BY_SYMBOL_SQL, (uid, sym))
            self._conn.commit()
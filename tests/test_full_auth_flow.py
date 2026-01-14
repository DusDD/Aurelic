from auth.register import register_user
from auth.login import login_user
from auth.delete import delete_user
from src.stocks.db_calls import get_stock_prices

# --- 1️⃣ Test-Konfiguration ---
username = "testuser5"
passwords_to_test = [
    "short",                  # zu kurz
    "nouppercase123!",        # kein Großbuchstabe
    "NOLOWERCASE123!",        # kein Kleinbuchstabe
    "NoNumber!",              # keine Zahl
    "NoSpecial123",           # kein Sonderzeichen
    "Very$ecure123Password!"  # gültiges Passwort
]

# --- 2️⃣ Schleife über Passwörter ---
for password in passwords_to_test:
    print("\n===================================")
    print(f"Versuche Registrierung für {username} mit Passwort: {password}")

    # Registrierung
    reg_result = register_user(username, password)
    print("Registrierungsergebnis:", reg_result)

    if not reg_result["success"]:
        print("Registrierung fehlgeschlagen, Grund:", reg_result["error"])
        continue  # nächstes Passwort testen

    # Login
    print("\nVersuche Login...")
    login_result = login_user(username, password)
    print("Login-Ergebnis:", login_result)

    if not login_result["success"]:
        print("Login fehlgeschlagen:", login_result["error"])
        continue

    token = login_result["token"]
    print("JWT-Token erhalten:", token)

    # Zugriff auf Aktiendaten
    try:
        prices = get_stock_prices(token, "AAPL")
        print("\nErste 5 Aktiendaten:", prices[:5])
    except Exception as e:
        print("Fehler beim Zugriff auf Aktiendaten:", e)

    # Soft-Delete durchführen
    print("\nFühre Soft-Delete des Nutzers durch...")
    delete_result = delete_user(username)
    print("Soft-Delete Ergebnis:", delete_result)

    # Versuch erneut einzuloggen nach Soft-Delete
    print("\nVersuche Login nach Soft-Delete...")
    login_after_delete = login_user(username, password)
    print("Login nach Soft-Delete:", login_after_delete)

    # Nach dem ersten gültigen Passwort-Test abbrechen
    break

from auth.login import login_user
from auth.guard import require_auth
from auth.token import blacklist_token

# 1) Login
print("== LOGIN ==")
res = login_user("dudd@gmail.com", "Wayesxrdc1!")

print(res)

if not res["success"]:
    print("Login fehlgeschlagen")
    exit()

token = res["token"]
print("Token:", token)

# 2) Guard testen
print("\n== TOKEN PRÜFUNG ==")
try:
    user_id = require_auth(token)
    print("Token gültig! User-ID:", user_id)
except Exception as e:
    print("Token ungültig:", e)

# 3) Logout (Blacklist)
print("\n== LOGOUT ==")
blacklist_token(token)
print("Token auf Blacklist gesetzt")

# 4) Erneute Prüfung
print("\n== TOKEN NACH LOGOUT ==")
try:
    user_id = require_auth(token)
    print("FEHLER: Token sollte ungültig sein!")
except Exception as e:
    print("OK - Token gesperrt:", e)
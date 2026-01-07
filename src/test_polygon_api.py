import os
from dotenv import load_dotenv
import requests

# 1. Lade die .env-Datei
load_dotenv()

# 2. Hole den Key aus der Umgebung
API_KEY = os.getenv("POLYGON_API_KEY")
if not API_KEY:
    raise ValueError("API_KEY nicht gefunden! Hast du die .env-Datei aktualisiert?")
# 3. Mach die API-Anfrage
url = "https://api.polygon.io/v2/aggs/ticker/AAPL/prev"
response = requests.get(url, params={"apiKey": API_KEY})
data = response.json()

print(data)
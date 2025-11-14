from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:meinpasswort@localhost:5432/stockapp')

try:
    with engine.connect() as conn:
        print("Verbindung mit SQLAlchemy erfolgreich!")
except Exception as e:
    print("Fehler:", e)
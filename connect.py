from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:meinpasswort@localhost:5432/stockapp')
print(engine.connect())

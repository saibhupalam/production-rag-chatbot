from sqlalchemy import text

from app.db.session import engine


try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))

        print(result.fetchone())

        print("Database connection successful!")

except Exception as e:
    print("Database connection failed!")
    print(e)
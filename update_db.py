
from sqlalchemy import text
from database import engine

with engine.connect() as connection:
    connection.execute(text(
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS "
        "customer_name VARCHAR(100)"
    ))

    connection.execute(text(
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS "
        "email VARCHAR(150)"
    ))

    connection.execute(text(
        "ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL"
    ))

    connection.commit()

print("Database updated successfully!")

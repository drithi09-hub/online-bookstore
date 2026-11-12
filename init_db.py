
from database import engine, Base
import models

def create_tables():
    print("Connecting to PostgreSQL...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")
    print("Tables:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    create_tables()

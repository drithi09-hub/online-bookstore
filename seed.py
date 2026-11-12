
from database import SessionLocal
from models import Book

books = [
    {"title": "Atomic Habits", "author": "James Clear", "price": 14.99, "category": "Self Help", "emoji": "📘"},
    {"title": "The Alchemist", "author": "Paulo Coelho", "price": 11.99, "category": "Fiction", "emoji": "✨"},
    {"title": "Rich Dad Poor Dad", "author": "Robert Kiyosaki", "price": 13.99, "category": "Finance", "emoji": "💰"},
    {"title": "Ikigai", "author": "Hector Garcia", "price": 12.50, "category": "Self Help", "emoji": "🌿"},
    {"title": "The Psychology of Money", "author": "Morgan Housel", "price": 15.99, "category": "Finance", "emoji": "🧠"},
    {"title": "Harry Potter", "author": "J.K. Rowling", "price": 18.99, "category": "Fantasy", "emoji": "🪄"},
    {"title": "It Ends With Us", "author": "Colleen Hoover", "price": 13.50, "category": "Romance", "emoji": "❤️"},
    {"title": "Deep Work", "author": "Cal Newport", "price": 14.50, "category": "Productivity", "emoji": "📚"},
]

db = SessionLocal()

try:
    for book_data in books:
        existing = db.query(Book).filter(
            Book.title == book_data["title"]
        ).first()

        if not existing:
            db.add(Book(**book_data))

    db.commit()
    print("Books inserted successfully!")

    all_books = db.query(Book).all()
    print("Total books in database:", len(all_books))

finally:
    db.close()

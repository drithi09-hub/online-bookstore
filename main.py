
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="Online Bookstore")

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# Sample bookstore inventory with USD prices
books = [
    {"id": 1, "title": "Atomic Habits", "author": "James Clear", "price": 14.99, "category": "Self Help", "emoji": "📘"},
    {"id": 2, "title": "The Alchemist", "author": "Paulo Coelho", "price": 11.99, "category": "Fiction", "emoji": "✨"},
    {"id": 3, "title": "Rich Dad Poor Dad", "author": "Robert Kiyosaki", "price": 13.99, "category": "Finance", "emoji": "💰"},
    {"id": 4, "title": "Ikigai", "author": "Hector Garcia", "price": 12.50, "category": "Self Help", "emoji": "🌿"},
    {"id": 5, "title": "The Psychology of Money", "author": "Morgan Housel", "price": 15.99, "category": "Finance", "emoji": "🧠"},
    {"id": 6, "title": "Harry Potter", "author": "J.K. Rowling", "price": 18.99, "category": "Fantasy", "emoji": "🪄"},
    {"id": 7, "title": "It Ends With Us", "author": "Colleen Hoover", "price": 13.50, "category": "Romance", "emoji": "❤️"},
    {"id": 8, "title": "Deep Work", "author": "Cal Newport", "price": 14.50, "category": "Productivity", "emoji": "📚"},
]

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "templates" / "index.html")

@app.get("/api/books")
def get_books():
    return books

@app.get("/api/health")
def health():
    return {
        "status": "running",
        "message": "Online Bookstore API is working"
    }

class OrderRequest(BaseModel):
    customer_name: str
    email: str
    items: list[dict]

@app.post("/api/orders")
def place_order(order: OrderRequest):
    if not order.items:
        return {
            "success": False,
            "message": "Your cart is empty"
        }

    total = round(sum(
        float(item.get("price", 0)) * int(item.get("quantity", 1))
        for item in order.items
    ), 2)

    return {
        "success": True,
        "message": "Order placed successfully! Payment simulated.",
        "customer": order.customer_name,
        "total": total
    }

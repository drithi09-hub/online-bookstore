
import os
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import get_db
from user_factory import UserFactory
from order_state import Order as OrderStateContext

from payment_strategy import (
    PaymentContext,
    CardPayment,
    PayPalPayment,
    CashOnDelivery
)

from observer import OrderSubject, CustomerNotifier


app = FastAPI(title="BookNest Online Bookstore")

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


# OBSERVER PATTERN SETUP
order_subject = OrderSubject()
customer_notifier = CustomerNotifier()
order_subject.attach(customer_notifier)


# REQUEST MODELS
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class OrderRequest(BaseModel):
    customer_name: str
    email: str
    items: list[dict]
    payment_method: str = "card"


class BookRequest(BaseModel):
    title: str
    author: str
    price: float
    category: str
    emoji: str = "📘"


# ADMIN AUTHENTICATION
def verify_admin(x_admin_key: str = Header(default="")):
    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key or x_admin_key != admin_key:
        raise HTTPException(
            status_code=403,
            detail="Admin access denied"
        )


# HOME PAGE
@app.get("/")
def home():
    return FileResponse(BASE_DIR / "templates" / "index.html")


# DISPLAY BOOKS
@app.get("/api/books")
def get_books(db: Session = Depends(get_db)):
    books = db.query(models.Book).order_by(models.Book.id).all()

    return [
        {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "price": book.price,
            "category": book.category,
            "emoji": book.emoji
        }
        for book in books
    ]


# ADMIN - ADD BOOK
@app.post("/api/books")
def add_book(
    book_data: BookRequest,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)
):
    new_book = models.Book(
        title=book_data.title,
        author=book_data.author,
        price=book_data.price,
        category=book_data.category,
        emoji=book_data.emoji
    )

    try:
        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        return {
            "success": True,
            "message": "Book added successfully!",
            "book_id": new_book.id
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to add book"
        )


# ADMIN - UPDATE BOOK
@app.put("/api/books/{book_id}")
def update_book(
    book_id: int,
    book_data: BookRequest,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)
):
    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    book.title = book_data.title
    book.author = book_data.author
    book.price = book_data.price
    book.category = book_data.category
    book.emoji = book_data.emoji

    try:
        db.commit()

        return {
            "success": True,
            "message": "Book updated successfully!"
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update book"
        )


# ADMIN - DELETE BOOK
@app.delete("/api/books/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)
):
    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    existing_item = db.query(models.OrderItem).filter(
        models.OrderItem.book_id == book_id
    ).first()

    if existing_item:
        raise HTTPException(
            status_code=400,
            detail="This book belongs to an existing order and cannot be deleted"
        )

    try:
        db.delete(book)
        db.commit()

        return {
            "success": True,
            "message": "Book deleted successfully!"
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to delete book"
        )


# USER REGISTRATION - FACTORY PATTERN
@app.post("/api/register")
def register_user(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    if not user_data.name.strip() or not user_data.email.strip():
        raise HTTPException(
            status_code=400,
            detail="Name and email are required"
        )

    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    email = user_data.email.strip().lower()

    existing_user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = UserFactory.create_user(
        name=user_data.name.strip(),
        email=email,
        password=user_data.password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "message": "Registration successful!",
            "user_id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to register user"
        )


# USER LOGIN
@app.post("/api/login")
def login_user(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == login_data.email.strip().lower()
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = UserFactory.password_hash.verify(
        login_data.password,
        user.password
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "success": True,
        "message": "Login successful!",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


# PLACE ORDER - STRATEGY + OBSERVER PATTERNS
@app.post("/api/orders")
def place_order(
    order: OrderRequest,
    db: Session = Depends(get_db)
):
    if not order.items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty"
        )

    payment_strategies = {
        "card": CardPayment(),
        "paypal": PayPalPayment(),
        "cash_on_delivery": CashOnDelivery()
    }

    payment_method = order.payment_method.lower()

    if payment_method not in payment_strategies:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment method"
        )

    total = 0
    order_items = []

    for item in order.items:
        try:
            book_id = int(item.get("id", 0))
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid book ID or quantity"
            )

        if quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid quantity"
            )

        book = db.query(models.Book).filter(
            models.Book.id == book_id
        ).first()

        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID {book_id} not found"
            )

        total += book.price * quantity

        order_items.append({
            "book_id": book.id,
            "quantity": quantity,
            "price": book.price
        })

    total = round(total, 2)

    # STRATEGY PATTERN
    payment_context = PaymentContext(
        payment_strategies[payment_method]
    )

    payment_result = payment_context.process_payment(total)

    if not payment_result["success"]:
        raise HTTPException(
            status_code=400,
            detail="Payment failed"
        )

    try:
        new_order = models.Order(
            customer_name=order.customer_name,
            email=order.email,
            total_amount=total,
            status="PLACED"
        )

        db.add(new_order)
        db.flush()

        for item in order_items:
            db.add(models.OrderItem(
                order_id=new_order.id,
                book_id=item["book_id"],
                quantity=item["quantity"],
                price=item["price"]
            ))

        db.commit()
        db.refresh(new_order)

        # OBSERVER PATTERN
        order_subject.notify_observers(
            new_order.id,
            order.email,
            f"Your BookNest order #{new_order.id} was placed successfully!"
        )

        return {
            "success": True,
            "message": "Order placed successfully!",
            "order_id": new_order.id,
            "customer": order.customer_name,
            "total": total,
            "payment": payment_result,
            "notification": "Customer notification triggered successfully"
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to place order"
        )


# TRACK ORDER
@app.get("/api/orders/{order_id}")
def track_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return {
        "order_id": order.id,
        "customer_name": order.customer_name,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at
    }


# UPDATE ORDER STATUS - STATE PATTERN
@app.patch("/api/orders/{order_id}/next-status")
def update_order_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    try:
        order_context = OrderStateContext(order.status)
        order_context.move_to_next_state()

        order.status = order_context.get_status()

        db.commit()
        db.refresh(order)

        return {
            "success": True,
            "message": "Order status updated successfully!",
            "order_id": order.id,
            "new_status": order.status
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update order status"
        )


# HEALTH CHECK
@app.get("/api/health")
def health():
    return {
        "status": "running",
        "message": "BookNest API is working"
    }

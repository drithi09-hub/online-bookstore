
let allBooks = [];
let cart = [];
let selectedCategory = "All";

// Load books from backend
async function loadBooks() {
    try {
        const response = await fetch("/api/books");
        allBooks = await response.json();
        renderBooks();
    } catch (error) {
        document.getElementById("book-grid").innerHTML =
            "<p>Unable to load books. Please refresh the page.</p>";
    }
}

// Display books
function renderBooks() {
    const search = document.getElementById("search").value.toLowerCase();

    const filtered = allBooks.filter(book => {
        const matchesSearch =
            book.title.toLowerCase().includes(search) ||
            book.author.toLowerCase().includes(search);

        const matchesCategory =
            selectedCategory === "All" ||
            book.category === selectedCategory;

        return matchesSearch && matchesCategory;
    });

    const grid = document.getElementById("book-grid");

    if (filtered.length === 0) {
        grid.innerHTML = "<p>No books found.</p>";
        return;
    }

    grid.innerHTML = filtered.map(book => `
        <div class="book-card">
            <div class="book-cover">${book.emoji}</div>
            <div class="book-info">
                <p class="category">${book.category}</p>
                <h3>${book.title}</h3>
                <p class="author">By ${book.author}</p>

                <div class="book-bottom">
                    <span class="price">$${Number(book.price).toFixed(2)}</span>

                    <button class="add-button" onclick="addToCart(${book.id})">
                        + Add
                    </button>
                </div>
            </div>
        </div>
    `).join("");
}

// Filter books by category
function setCategory(category, button) {
    selectedCategory = category;

    document.querySelectorAll(".filter").forEach(item => {
        item.classList.remove("active");
    });

    button.classList.add("active");
    renderBooks();
}

// Add book to cart
function addToCart(bookId) {
    const book = allBooks.find(item => item.id === bookId);
    const existing = cart.find(item => item.id === bookId);

    if (existing) {
        existing.quantity++;
    } else {
        cart.push({...book, quantity: 1});
    }

    updateCartCount();
    alert(book.title + " added to your cart!");
}

// Update cart count
function updateCartCount() {
    const count = cart.reduce(
        (sum, item) => sum + item.quantity, 0
    );

    document.getElementById("cart-count").textContent = count;
}

// Show shopping cart
function showCart() {
    const modal = document.getElementById("cart-modal");
    const items = document.getElementById("cart-items");

    modal.classList.add("show");

    if (cart.length === 0) {
        items.innerHTML = "<p>Your cart is empty. Explore some books!</p>";

        document.getElementById("cart-total").textContent = "Total: $0.00";
        return;
    }

    items.innerHTML = cart.map(item => `
        <div class="cart-row">
            <div>
                <strong>${item.title}</strong>
                <p>$${Number(item.price).toFixed(2)} × ${item.quantity}</p>
            </div>

            <div>
                <button onclick="changeQuantity(${item.id}, -1)">−</button>

                ${item.quantity}

                <button onclick="changeQuantity(${item.id}, 1)">+</button>

                <button onclick="removeFromCart(${item.id})">Remove</button>
            </div>
        </div>
    `).join("");

    const total = cart.reduce(
        (sum, item) => sum + item.price * item.quantity, 0
    );

    document.getElementById("cart-total").textContent =
        "Total: $" + total.toFixed(2);
}

// Increase or decrease quantity
function changeQuantity(bookId, change) {
    const item = cart.find(book => book.id === bookId);

    if (item) {
        item.quantity += change;

        if (item.quantity <= 0) {
            removeFromCart(bookId);
            return;
        }
    }

    updateCartCount();
    showCart();
}

// Remove book from cart
function removeFromCart(bookId) {
    cart = cart.filter(item => item.id !== bookId);

    updateCartCount();
    showCart();
}

// Close shopping cart
function closeCart() {
    document.getElementById("cart-modal").classList.remove("show");
}

// Checkout
async function checkout() {
    if (cart.length === 0) {
        alert("Your cart is empty!");
        return;
    }

    const customerName = prompt("Enter your full name:");

    if (!customerName || !customerName.trim()) return;

    const email = prompt("Enter your email address:");

    if (!email || !email.trim()) return;

    try {
        const response = await fetch("/api/orders", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                customer_name: customerName.trim(),
                email: email.trim(),

                items: cart.map(item => ({
                    id: item.id,
                    price: item.price,
                    quantity: item.quantity
                }))
            })
        });

        const result = await response.json();

        if (result.success) {
            alert(
                result.message +
                "\nOrder total: $" + Number(result.total).toFixed(2)
            );

            cart = [];

            updateCartCount();
            closeCart();

        } else {
            alert(result.message);
        }

    } catch (error) {
        alert("Checkout failed. Please try again.");
    }
}

// Start the website
loadBooks();

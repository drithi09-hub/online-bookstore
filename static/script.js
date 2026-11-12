
let allBooks = [];
let cart = [];
let selectedCategory = "All";
let authMode = "login";
let currentUser = JSON.parse(localStorage.getItem("booknestUser") || "null");


// LOAD BOOKS
async function loadBooks() {
    try {
        const response = await fetch("/api/books");
        if (!response.ok) throw new Error("Unable to load books");

        allBooks = await response.json();
        renderBooks();
        renderAdminBooks();
        updateUserInterface();
    } catch (error) {
        document.getElementById("book-grid").innerHTML =
            "<p>Unable to load books. Please refresh.</p>";
    }
}


// DISPLAY BOOKS
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

    if (!filtered.length) {
        grid.innerHTML = "<p>No books found.</p>";
        return;
    }

    grid.innerHTML = filtered.map(book => `
        <div class="book-card">
            <div class="book-cover">${book.emoji || "📘"}</div>
            <div class="book-info">
                <p class="category">${book.category || "General"}</p>
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


// CATEGORY FILTER
function setCategory(category, button) {
    selectedCategory = category;

    document.querySelectorAll(".filter").forEach(item => {
        item.classList.remove("active");
    });

    button.classList.add("active");
    renderBooks();
}


// SHOPPING CART
function addToCart(bookId) {
    const book = allBooks.find(item => item.id === bookId);
    if (!book) return;

    const existing = cart.find(item => item.id === bookId);

    if (existing) {
        existing.quantity++;
    } else {
        cart.push({...book, quantity: 1});
    }

    updateCartCount();
    alert(book.title + " added to your cart!");
}


function updateCartCount() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById("cart-count").textContent = count;
}


function showCart() {
    document.getElementById("cart-modal").classList.add("show");

    const items = document.getElementById("cart-items");

    if (!cart.length) {
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


function changeQuantity(bookId, change) {
    const item = cart.find(book => book.id === bookId);

    if (!item) return;

    item.quantity += change;

    if (item.quantity <= 0) {
        removeFromCart(bookId);
        return;
    }

    updateCartCount();
    showCart();
}


function removeFromCart(bookId) {
    cart = cart.filter(item => item.id !== bookId);
    updateCartCount();
    showCart();
}


function closeCart() {
    document.getElementById("cart-modal").classList.remove("show");
}


// LOGIN AND REGISTRATION
function showAuth() {
    document.getElementById("auth-modal").classList.add("show");
    setAuthMode("login");
}


function closeAuth() {
    document.getElementById("auth-modal").classList.remove("show");
}


function setAuthMode(mode) {
    authMode = mode;

    document.getElementById("auth-name").style.display =
        mode === "register" ? "block" : "none";

    document.getElementById("auth-password").placeholder =
        "Password (minimum 8 characters)";

    document.getElementById("auth-message").textContent =
        mode === "login" ? "Login to your account." : "Create a new account.";
}


async function submitAuth(event) {
    event.preventDefault();

    const name = document.getElementById("auth-name").value.trim();
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;

    const endpoint = authMode === "register"
        ? "/api/register"
        : "/api/login";

    const body = authMode === "register"
        ? {name, email, password}
        : {email, password};

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Authentication failed");
        }

        if (authMode === "register") {
            document.getElementById("auth-message").textContent =
                "Registration successful! Please log in.";
            setAuthMode("login");
            document.getElementById("auth-email").value = email;
            document.getElementById("auth-password").value = "";
            return;
        }

        currentUser = result;
        localStorage.setItem("booknestUser", JSON.stringify(currentUser));

        updateUserInterface();
        closeAuth();

        alert("Welcome, " + currentUser.name + "!");

    } catch (error) {
        document.getElementById("auth-message").textContent = error.message;
    }
}


function logout() {
    currentUser = null;
    localStorage.removeItem("booknestUser");
    updateUserInterface();
    alert("You have logged out.");
}


function updateUserInterface() {
    const loginButton = document.querySelector("header .cart-button");

    if (currentUser) {
        loginButton.textContent = "Logout";
        loginButton.onclick = logout;
    } else {
        loginButton.textContent = "Login";
        loginButton.onclick = showAuth;
    }

    document.getElementById("admin").style.display =
        currentUser && currentUser.role === "admin" ? "block" : "none";
}


// CHECKOUT WITH PAYMENT STRATEGY
async function checkout() {
    if (!cart.length) {
        alert("Your cart is empty!");
        return;
    }

    const customerName = currentUser
        ? currentUser.name
        : prompt("Enter your full name:");

    if (!customerName || !customerName.trim()) return;

    const email = currentUser
        ? currentUser.email
        : prompt("Enter your email address:");

    if (!email || !email.trim()) return;

    const paymentMethod =
        document.getElementById("payment-method").value;

    try {
        const response = await fetch("/api/orders", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                customer_name: customerName.trim(),
                email: email.trim(),
                payment_method: paymentMethod,
                items: cart.map(item => ({
                    id: item.id,
                    quantity: item.quantity
                }))
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Checkout failed");
        }

        alert(
            result.message +
            "\nOrder ID: " + result.order_id +
            "\nTotal: $" + Number(result.total).toFixed(2) +
            "\nPayment: " + result.payment.method
        );

        document.getElementById("track-order-id").value = result.order_id;

        cart = [];
        updateCartCount();
        closeCart();

    } catch (error) {
        alert(error.message);
    }
}


// ORDER TRACKING
async function trackOrder() {
    const orderId = document.getElementById("track-order-id").value;
    const resultBox = document.getElementById("order-result");

    if (!orderId) {
        alert("Please enter an order ID.");
        return;
    }

    resultBox.textContent = "Checking order...";

    try {
        const response = await fetch(`/api/orders/${orderId}`);

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Order not found");
        }

        resultBox.innerHTML = `
            <h3>Order #${result.order_id}</h3>
            <p>Customer: ${result.customer_name}</p>
            <p>Total: $${Number(result.total_amount).toFixed(2)}</p>
            <p><strong>Status: ${result.status}</strong></p>
        `;

    } catch (error) {
        resultBox.textContent = error.message;
    }
}


// ADMIN BOOK MANAGEMENT
function renderAdminBooks() {
    const list = document.getElementById("admin-book-list");

    if (!list) return;

    if (!currentUser || currentUser.role !== "admin") {
        list.innerHTML = "";
        return;
    }

    list.innerHTML = allBooks.map(book => `
        <div class="admin-book-row">
            <span>${book.title} - $${Number(book.price).toFixed(2)}</span>
            <div>
                <button onclick="editBook(${book.id})">Edit</button>
                <button onclick="deleteBook(${book.id})">Delete</button>
            </div>
        </div>
    `).join("");
}


async function addBook(event) {
    event.preventDefault();
    alert("Add Book function is working!");

    if (!currentUser || currentUser.role !== "admin") {
        alert("Admin access required.");
        return;
    }

    const book = {
        title: document.getElementById("book-title").value.trim(),
        author: document.getElementById("book-author").value.trim(),
        price: Number(document.getElementById("book-price").value),
        category: document.getElementById("book-category").value.trim(),
        emoji: document.getElementById("book-emoji").value.trim() || "📘"
    };

    await saveBook("/api/books", "POST", book);
    document.getElementById("book-form").reset();
}


async function editBook(id) {
    const book = allBooks.find(item => item.id === id);
    if (!book) return;

    const title = prompt("Enter book title:", book.title);
    if (title === null) return;

    const author = prompt("Enter author:", book.author);
    if (author === null) return;

    const price = prompt("Enter price:", book.price);
    if (price === null) return;

    const category = prompt("Enter category:", book.category);
    if (category === null) return;

    const emoji = prompt("Enter emoji:", book.emoji || "📘");
    if (emoji === null) return;

    await saveBook(`/api/books/${id}`, "PUT", {
        title: title.trim(),
        author: author.trim(),
        price: Number(price),
        category: category.trim(),
        emoji: emoji.trim()
    });
}


async function deleteBook(id) {
    if (!confirm("Are you sure you want to delete this book?")) return;

    await saveBook(`/api/books/${id}`, "DELETE");
}


   
async function saveBook(url, method, book = null) {
    alert("saveBook function started!");
    try {
        let adminKey = sessionStorage.getItem("booknestAdminKey");

        if (!adminKey) {
            adminKey = prompt("Enter your BookNest Admin API Key:");

            if (!adminKey) {
                alert("Admin key is required.");
                return;
            }

            sessionStorage.setItem("booknestAdminKey", adminKey);
        }

        const options = {
            method,
            headers: {
                "Content-Type": "application/json",
                "X-Admin-Key": adminKey
            }
        };

        if (book) {
            options.body = JSON.stringify(book);
        }

        const response = await fetch(url, options);
        const result = await response.json();

        if (!response.ok) {
            if (response.status === 403) {
                sessionStorage.removeItem("booknestAdminKey");
                throw new Error("Invalid admin key. Please try again.");
            }

            throw new Error(result.detail || "Book operation failed");
        }

        alert(result.message || "Book operation successful!");

        await loadBooks();

    } catch (error) {
        alert(error.message);
    }
}



// START WEBSITE
loadBooks();

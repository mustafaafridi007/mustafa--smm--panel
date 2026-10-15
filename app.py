
from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary-demo-key")

def connect_db():
    con = sqlite3.connect("smm.db")
    con.row_factory = sqlite3.Row
    return con

with connect_db() as con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            link TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

def page(content):
    return f"""
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body {{background:#101827;color:white;font-family:Arial;
    max-width:600px;margin:30px auto;padding:18px}}
    input,select,button {{width:100%;padding:12px;margin:8px 0;
    box-sizing:border-box;border-radius:8px}}
    button {{background:#00d6a0;border:0;font-weight:bold}}
    a {{color:#00d6a0}}
    .card {{background:#202c40;padding:15px;border-radius:12px;
    margin:12px 0}}
    </style>
    <h1>Mustafa SMM Panel</h1>{content}
    """

@app.route("/")
def home():
    return page("""
    <div class="card">
    <h2>Social Media Services</h2>
    <p>TikTok Likes | Instagram Likes | YouTube Views</p>
    <a href="/signup">Create Account</a><br><br>
    <a href="/login">Login</a>
    </div>
    """)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if len(username) < 3 or len(password) < 8:
            message = "Username 3+ aur password 8+ characters rakhein."
        else:
            try:
                with connect_db() as con:
                    con.execute(
                        "INSERT INTO users(username,password) VALUES(?,?)",
                        (username, generate_password_hash(password))
                    )
                return redirect("/login")
            except sqlite3.IntegrityError:
                message = "Ye username pehle se mojood hai."

    return page(f"""
    <h2>Signup</h2><p>{message}</p>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password"
    placeholder="Password (8+ characters)" required>
    <button>Create Account</button>
    </form><a href="/login">Login</a>
    """)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        with connect_db() as con:
            user = con.execute(
                "SELECT * FROM users WHERE username=?",
                (request.form["username"].strip(),)
            ).fetchone()
        if user and check_password_hash(
            user["password"], request.form["password"]
        ):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")
        message = "Username ya password ghalat hai."

    return page(f"""
    <h2>Login</h2><p>{message}</p>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Login</button>
    </form><a href="/signup">Create Account</a>
    """)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    with connect_db() as con:
        orders = con.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()

    order_list = "".join(
        f"<div class='card'>Order #{o['id']} — {o['service']}<br>"
        f"Quantity: {o['quantity']}<br>Status: {o['status']}</div>"
        for o in orders
    ) or "<p>Abhi koi order nahi.</p>"

    return page(f"""
    <h2>Welcome, {session['username']}!</h2>
    <div class="card"><h3>Demo Order</h3>
    <form method="post" action="/order">
    <select name="service">
    <option>TikTok Likes</option>
    <option>Instagram Likes</option>
    <option>YouTube Views</option>
    </select>
    <input name="link" type="url" placeholder="Public post URL" required>
    <input name="quantity" type="number" min="100" max="10000"
    placeholder="Quantity" required>
    <button>Place Demo Order</button>
    </form></div>
    <h3>Your Orders</h3>{order_list}
    <a href="/logout">Logout</a>
    """)

@app.route("/order", methods=["POST"])
def order():
    if "user_id" not in session:
        return redirect("/login")
    service = request.form["service"]
    link = request.form["link"].strip()
    try:
        quantity = int(request.form["quantity"])
    except ValueError:
        return "Invalid quantity", 400

    if service not in (
        "TikTok Likes", "Instagram Likes", "YouTube Views"
    ) or not link.startswith("https://") or not 100 <= quantity <= 10000:
        return "Invalid order details", 400

    with connect_db() as con:
        con.execute(
            """INSERT INTO orders(user_id,service,link,quantity)
            VALUES(?,?,?,?)""",
            (session["user_id"], service, link, quantity)
        )
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)


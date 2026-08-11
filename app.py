from flask import Flask, render_template, request, redirect, session
import sqlite3
from tavily import TavilyClient
"sk-tinyfish-mR4a7hrA6TRq3el_vKea_QSh6JYoqzUi"
import os
tavily_client = TavilyClient(
    api_key=os.environ.get("TAVILY_API_KEY")
)


def online_search(query):

    results = tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=5
    )

    return results["results"]
app = Flask(__name__)

app.secret_key = "agriconnect-secret-key"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("agriconnect.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            village TEXT
        )
    """)

    # Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT,
            price REAL NOT NULL,
            type TEXT NOT NULL,
            location TEXT
        )
    """)

    # Default user
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        ("farmer",)
    ).fetchone()

    if user is None:

        conn.execute(
            """
            INSERT INTO users
            (name, username, password, village)
            VALUES (?, ?, ?, ?)
            """,
            ("Farmer", "farmer", "1234", "My Village")
        )

    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE username = ? AND password = ?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]

            return redirect("/home")

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# ---------------- HOME ----------------

@app.route("/home")
def home():

    if "user_id" not in session:
        return redirect("/")

    return render_template(
        "home.html",
        name=session["name"]
    )


# ---------------- PRODUCTS ----------------

    
@app.route("/products")
def products():

    if "user_id" not in session:
        return redirect("/")

    search = request.args.get("search", "").strip()

    online_results = []

    if search:

        try:

            online_results = online_search(search)

        except Exception as e:

            print("Online search error:", e)

    return render_template(
        "products.html",
        products=[],
        search=search,
    online_results=online_results
    )




# ---------------- ADD PRODUCT ----------------

@app.route("/add-product", methods=["GET", "POST"])
def add_product():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        brand = request.form["brand"]
        price = request.form["price"]
        product_type = request.form["type"]
        location = request.form["location"]

        conn = get_db()

        conn.execute(
            """
            INSERT INTO products
            (name, category, brand, price, type, location)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                category,
                brand,
                price,
                product_type,
                location
            )
        )

        conn.commit()
        conn.close()

        return redirect("/products")

    return render_template("add_product.html")


# ---------------- PROFILE ----------------

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- START APP ----------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)
from flask import Flask, render_template, request, redirect, session
import sqlite3
from tavily import TavilyClient
import os

# ==================================================
# APP
# ==================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "agriconnect-secret-key"
)


# ==================================================
# TAVILY
# ==================================================

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


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db():

    conn = sqlite3.connect("agriconnect.db")

    conn.row_factory = sqlite3.Row

    return conn


# ==================================================
# CREATE DATABASE
# ==================================================

def create_database():

    conn = get_db()

    # --------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            village TEXT,
            phone TEXT,
            email TEXT
        )
    """)

    # --------------------------------------------------
    # PRODUCTS TABLE
    # --------------------------------------------------

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

    # --------------------------------------------------
    # DEFAULT USER
    # --------------------------------------------------

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        ("farmer",)
    ).fetchone()

    if user is None:

        conn.execute(
            """
            INSERT INTO users
            (
                name,
                username,
                password,
                village,
                phone,
                email
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Farmer",
                "raghuram",
                "9392",
                "Sathupally",
                "",
                ""
            )
        )

    # --------------------------------------------------
    # DEFAULT PRODUCTS
    # --------------------------------------------------

    products = [

        # TRACTORS

        (
            "Mahindra 575 DI",
            "Tractor",
            "Mahindra",
            750000,
            "45 HP",
            "Sathupally"
        ),

        (
            "John Deere 5310",
            "Tractor",
            "John Deere",
            950000,
            "55 HP",
            "Sathupally"
        ),

        (
            "Swaraj 744 FE",
            "Tractor",
            "Swaraj",
            800000,
            "48 HP",
            "Sathupally"
        ),

        # IMPLEMENTS

        (
            "Rotavator",
            "Implement",
            "Shaktiman",
            120000,
            "Agricultural Implement",
            "Sathupally"
        ),

        (
            "Cultivator",
            "Implement",
            "Mahindra",
            45000,
            "Agricultural Implement",
            "Sathupally"
        ),

        (
            "Disc Plough",
            "Implement",
            "Fieldking",
            65000,
            "Agricultural Implement",
            "Sathupally"
        ),

        # FERTILIZERS

        (
            "Urea",
            "Fertilizer",
            "IFFCO",
            300,
            "Nitrogen Fertilizer",
            "Sathupally"
        ),

        (
            "DAP",
            "Fertilizer",
            "IFFCO",
            1350,
            "Phosphorus Fertilizer",
            "Sathupally"
        ),

        (
            "MOP",
            "Fertilizer",
            "Coromandel",
            1700,
            "Potassium Fertilizer",
            "Sathupally"
        ),

        # SEEDS

        (
            "Paddy Seeds",
            "Seed",
            "Kaveri",
            500,
            "Rice Seeds",
            "Sathupally"
        ),

        (
            "Maize Seeds",
            "Seed",
            "Pioneer",
            700,
            "Maize Seeds",
            "Sathupally"
        ),

        (
            "Cotton Seeds",
            "Seed",
            "Rasi",
            800,
            "Cotton Seeds",
            "Sathupally"
        )
    ]

    # --------------------------------------------------
    # INSERT PRODUCTS
    # --------------------------------------------------

    for product in products:

        exists = conn.execute(
            """
            SELECT id
            FROM products
            WHERE name = ?
            AND category = ?
            """,
            (
                product[0],
                product[1]
            )
        ).fetchone()

        if exists is None:

            conn.execute(
                """
                INSERT INTO products
                (
                    name,
                    category,
                    brand,
                    price,
                    type,
                    location
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                product
            )

    conn.commit()

    conn.close()


# ==================================================
# LOGIN
# ==================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (
                username,
                password
            )
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


# ==================================================
# HOME
# ==================================================

@app.route("/home")
def home():

    if "user_id" not in session:
        return redirect("/")

    return render_template(
        "home.html",
        name=session["name"]
    )


# ==================================================
# PRODUCTS
# ==================================================

@app.route("/products")
def products():

    if "user_id" not in session:
        return redirect("/")

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    online_results = []

    conn = get_db()

    if category:

        products = conn.execute(
            """
            SELECT *
            FROM products
            WHERE category = ?
            """,
            (category,)
        ).fetchall()

    else:

        products = conn.execute(
            """
            SELECT *
            FROM products
            """
        ).fetchall()

    conn.close()

    # ONLINE SEARCH

    if search:

        try:

            online_results = online_search(search)

        except Exception as e:

            print(
                "Online search error:",
                e
            )

    return render_template(
        "products.html",
        products=products,
        search=search,
        category=category,
        online_results=online_results
    )


# ==================================================
# ADD PRODUCT
# ==================================================

@app.route(
    "/add-product",
    methods=["GET", "POST"]
)
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
            (
                name,
                category,
                brand,
                price,
                type,
                location
            )
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

    return render_template(
        "add_product.html"
    )


# ==================================================
# PROFILE
# ==================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/")

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (
            session["user_id"],
        )
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ==================================================
# UPDATE PROFILE
# ==================================================

@app.route(
    "/update-profile",
    methods=["POST"]
)
def update_profile():

    if "user_id" not in session:
        return redirect("/")

    name = request.form["name"]
    username = request.form["username"]
    village = request.form["village"]
    phone = request.form["phone"]
    email = request.form["email"]

    conn = get_db()

    try:

        conn.execute(
            """
            UPDATE users
            SET
                name = ?,
                username = ?,
                village = ?,
                phone = ?,
                email = ?
            WHERE id = ?
            """,
            (
                name,
                username,
                village,
                phone,
                email,
                session["user_id"]
            )
        )

        conn.commit()

        session["name"] = name
        session["username"] = username

    except sqlite3.IntegrityError:

        conn.close()

        return render_template(
            "profile.html",
            error="Username already exists"
        )

    conn.close()

    return redirect("/profile")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==================================================
# TRACTORS
# ==================================================

@app.route("/tractors")
def tractors():

    tractors = [

        {
            "name": "Mahindra 575 DI",
            "hp": "45 HP",
            "price": "₹7,50,000"
        },

        {
            "name": "John Deere 5310",
            "hp": "55 HP",
            "price": "₹9,50,000"
        },

        {
            "name": "Swaraj 744 FE",
            "hp": "48 HP",
            "price": "₹8,00,000"
        }
    ]

    return render_template(
        "tractors.html",
        tractors=tractors
    )


# ==================================================
# IMPLEMENTS
# ==================================================

@app.route("/implements")
def implements():

    implements = [

        {
            "name": "Rotavator",
            "type": "Tillage Equipment",
            "price": "₹1,20,000"
        },

        {
            "name": "Cultivator",
            "type": "Tillage Equipment",
            "price": "₹45,000"
        },

        {
            "name": "Disc Plough",
            "type": "Tillage Equipment",
            "price": "₹65,000"
        }
    ]

    return render_template(
        "implements.html",
        implements=implements
    )


# ==================================================
# FERTILIZERS
# ==================================================

@app.route("/fertilizers")
def fertilizers():

    fertilizers = [

        {
            "name": "Urea",
            "type": "Nitrogen",
            "price": "₹300"
        },

        {
            "name": "DAP",
            "type": "Phosphorus",
            "price": "₹1,350"
        },

        {
            "name": "MOP",
            "type": "Potassium",
            "price": "₹1,700"
        }
    ]

    return render_template(
        "fertilizers.html",
        fertilizers=fertilizers
    )


# ==================================================
# SEEDS
# ==================================================

@app.route("/seeds")
def seeds():

    seeds = [

        {
            "name": "Paddy Seeds",
            "crop": "Rice",
            "price": "₹500"
        },

        {
            "name": "Maize Seeds",
            "crop": "Maize",
            "price": "₹700"
        },

        {
            "name": "Cotton Seeds",
            "crop": "Cotton",
            "price": "₹800"
        }
    ]

    return render_template(
        "seeds.html",
        seeds=seeds
    )


# ==================================================
# START APPLICATION
# ==================================================

create_database()


if __name__ == "__main__":

    app.run(
        debug=True
    )
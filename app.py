from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///library.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # To register user
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must provide password check", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords are different", 400)

        hash_Password = generate_password_hash(request.form.get("password"))

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Already a username
        if len(rows) != 0:
            return apology("Username already exists", 400)

        newUser = db.execute("INSERT INTO users (username, password) VALUES(?,?)", request.form.get("username"), hash_Password)
        session["user_id"] = newUser
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def books():
    """Show all books or search for books"""

    if request.method == "POST":
        search_query = request.form.get("search")

        # Books that match the search query
        books = db.execute("SELECT * FROM books WHERE title LIKE ?", "%" + search_query + "%")

    else:
        # If no search query, show first 12 books
        books = db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 12")

    return render_template("books.html", books=books)

@app.route("/hold", methods=["POST"])
@login_required
def hold_book():
    title = request.form.get("title")
    author = request.form.get("author")
    user_id = session["user_id"]

    # Check if the book is already held
    hold_again = db.execute("SELECT * FROM holds WHERE Title = ? AND user_id = ?", title, user_id)
    if hold_again:
        flash(f"Book '{title}' has already been holded.")
        return redirect("/")


    # Put into holds SQL Database
    db.execute("INSERT INTO holds (Title, Author, user_id) VALUES (?, ?, ?)", title, author, user_id)

    # Put into history SQL Database
    db.execute("INSERT INTO history (title, action, user_id) VALUES (?, 'Hold', ?)", title, user_id)

    flash(f"Book '{title}' has been added to your holds.")
    return redirect("/")

@app.route("/holds")
@login_required
def holds():
    # List of books on hold
    holds = db.execute("SELECT Title, Author FROM holds WHERE user_id = ?", session["user_id"])
    return render_template("holds.html", holds=holds)


@app.route("/unhold", methods=["POST"])
@login_required
def unhold():
    title = request.form.get("title")
    user_id = session["user_id"]

    # Remove the hold from the database
    db.execute("DELETE FROM holds WHERE Title = ? AND user_id = ?", title, user_id)

    # Put this in the history database
    db.execute("INSERT INTO history (title, action, user_id) VALUES (?, 'Unhold', ?)", title, user_id)

    flash(f"Book '{title}' has been removed from your holds.")
    return redirect("/holds")

@app.route("/history")
@login_required
def history():
    history = db.execute("SELECT title, action, timestamp FROM history WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])
    return render_template("history.html", history=history)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        review = request.form.get("review")
        user_id = session.get("user_id")

        # Insert review into the database
        if user_id and review:
            db.execute("INSERT INTO reviews (user_id, review) VALUES (?, ?)", user_id, review)
            message = "Thank you for your review!"

        return render_template("contact.html", message=message)

    return render_template("contact.html")

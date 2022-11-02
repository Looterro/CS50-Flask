import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    cash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]['cash']
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]['username']
    
    # Get all the users stocks and their amount
    stocks = db.execute("SELECT symbol, SUM (shares) FROM orders WHERE username = ? GROUP BY symbol", user)

    # Return a dictionary with values required to display all the bought stocks and their current prices
    objects = []
    total = cash

    for stock in stocks:
        item = lookup(stock["symbol"])

        # Do not display a stock if no longer holding any shares
        if not stock["SUM (shares)"] == 0:
            object = {
                "symbol": stock["symbol"],
                "price": item["price"],
                "amount": stock["SUM (shares)"],
                "total": stock["SUM (shares)"] * item["price"],
            }
            objects.append(object)

    for object in objects:
        total += object["price"] * object["amount"]

    return render_template("index.html", stocks=stocks, objects=objects, total=total, cash=cash, user=user)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]['username']
    cash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    
    if request.method == "POST":
        
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        result = lookup(symbol)

        if shares < 0:
            return apology("Must provide a positive number")

        if result == None:
            return apology("Invalid symbol")
        
        stock_price = result['price'] * shares

        # Allow for the purchase only if funds available
        if cash > stock_price:

            # Deduct the cash from the user
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - stock_price, session["user_id"])

            # Add current time to purchase
            time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

            # Update "buy" table with purchase
            db.execute("INSERT INTO orders (datetime, username, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?, ?)", time, user, symbol, shares, result['price'], "BUY")

            return redirect("/")
        
        else:

            return apology("Insuficient funds")

    else:

        return render_template("buy.html", cash=cash)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]['username']
    orders = db.execute("SELECT * FROM orders WHERE username = ?", user)

    return render_template("history.html", orders=orders)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        
        symbol = request.form.get("symbol")
        result = lookup(symbol)

        if result == None:
            return apology("Invalid symbol")

        return render_template("quoted.html", result=result)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Get data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Make sure passwords match
        if password != confirmation:
            return apology("passwords dont match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if not request.form.get("username") or username == rows:
            return apology("must provide username or username already taken", 403)

        hash = generate_password_hash(password)

        # Remember registrant
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        return redirect("/")
    
    else:
        
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]['username']
    cash = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    current_stocks = db.execute("SELECT symbol, SUM (shares) FROM orders WHERE username = ? GROUP BY symbol", user)

    objects = []

    # Do not display a stock if no longer holding any shares
    for stock in current_stocks:
        if not stock["SUM (shares)"] == 0:
            objects.append(stock["symbol"])

    if request.method == "POST":
        
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        result = lookup(symbol)

        # Get all the users stocks and their amount
        amount_shares = int(db.execute("SELECT symbol, SUM (shares) FROM orders WHERE username = ? AND symbol = ? GROUP BY symbol", user, symbol)[0]["SUM (shares)"])

        if shares < 0:
            return apology("Must provide a positive number")

        if result == None:
            return apology("Invalid symbol")
        
        #Check if users sell more stock than they own
        if shares > amount_shares:
            return apology("You dont have enough shares to fulfill the order")
        
        sell_income = result['price'] * shares

        #Allow for the sell only if the stock is owned by the user
        if symbol in objects:

            # Deduct the cash from the user
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + sell_income, session["user_id"])

            # Add current time to sell
            time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

            # Update "buy" table with sell order
            db.execute("INSERT INTO orders (datetime, username, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?, ?)", time, user, symbol, -shares, result['price'], "SELL")

            return redirect("/")
        
        else:

            return apology("You dont have any shares from that stock")

    else:

        return render_template("sell.html", cash=cash, objects=objects)

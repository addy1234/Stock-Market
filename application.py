import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    #print("one")
    if request.method == "POST":
        #print("hello")
        if not request.form.get("symbol"):
            return apology("please provide symbol")
        if not request.form.get("shares"):
            return apology("please provide shares")
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        #print(type(shares))
        if int(shares) < 0:
            return apology("shares should be greater than 0")
        info = lookup(symbol)
        if not info["symbol"]:
            return apology("Symbol not existed")
        money = db.execute("SELECT cash FROM users WHERE id=:id",id=session['user_id'])
        #print(money.shape)
        if float(money[0]["cash"]) < float(shares) * info['price']:
            return apology("Sorry u don't have enough money to buy these shares")
        db.execute("INSERT INTO history('id','symbol','shares','cost','mode') VALUES(:id,:symbol,:shares,:cost,:mode)",
                    id = session["user_id"],symbol=symbol,shares=shares,cost=info['price'],mode='buy')
        purchase = float(shares)*info['price']
        db.execute("UPDATE users SET cash = cash - :purchase WHERE id=:id",
        purchase=purchase,id=session["user_id"])
        return render_template("bought.html" ,symbol=symbol, shares=shares, cost=info['price'])
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM history WHERE id=:id",id=session["user_id"])
    #print(transactions)
    return render_template("history.html" , transactions=transactions)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        #print(help(session))
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
        if not request.form.get("symbol"):
            return apology("Please Enter the Symbol")
        else:
            symbol = request.form.get("symbol")
            info = lookup(symbol)
            return render_template("quoted.html",name=info["name"],symbol=info["symbol"],price=info["price"])
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username",403)
        elif not request.form.get("password"):
            return apology("must provide password",403)
        rows = db.execute("SELECT * FROM users WHERE username = :username",username=request.form.get("username"))
        print(rows)
        if rows:
            return render_template("already.html")
        else:
            #print("world")
            username = request.form.get("username")
            password = request.form.get("password")
            hashValue = generate_password_hash(password)
            db.execute("INSERT INTO users('username','hash') VALUES(:username,:hash)" , username=username,hash=hashValue)
            return redirect('/login')
            # sql_statement = "INSERT INTO users('id','username','hash') VALUES(%s,%s,%s)"
            # db.execute(sql_statement,(2,username,hashValue))
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
     if request.method=="POST":
         if not request.form.get("symbol"):
             apology("Symbol not inputted")
         if not request.form.get("shares"):
             apology("Shares not inputted")
         symbol = request.form.get("symbol")
         shares = request.form.get("shares")
         if int(shares) < 0:
            return apology("shares should be greater than 0")
         info = lookup(symbol)
         if not info["symbol"]:
            return apology("Symbol not existed")
         db.execute("INSERT INTO history('id','symbol','shares','cost','mode') VALUES(:id,:symbol,:shares,:cost,:mode)",
         id = session["user_id"],symbol=symbol,shares=shares,cost=info['price'],mode='sell')
         purchase = float(shares)*info['price']
         db.execute("UPDATE users SET cash = cash + :purchase WHERE id=:id",
         purchase=purchase,id=session["user_id"])
         return render_template("sold.html" ,symbol=symbol, shares=shares, cost=info['price'])
     else:
         return render_template("sell.html")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

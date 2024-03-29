import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import urllib.request
import re
from os import path

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

ROOT = path.dirname(path.realpath(__file__))
DATABASE = 'final-project.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(path.join(ROOT, DATABASE))
    db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    get_db().commit()
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

average = 0
song = {}
video = ""
score = -1


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def search(artist, name):
    query_string = urllib.parse.urlencode({"search_query" : artist + name})
    html_content = urllib.request.urlopen("https://www.youtube.com.hk/results?"+query_string)
    search_results = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_content.read().decode())
    if search_results:
        search_results[0] = search_results[0].split("\\", 1)[0]

        return "https://www.youtube.com/embed/" + search_results[0]


def update_current_info():
    # Query database for current information
    global song
    global video
    global score
    
    user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)

    song["artist"] = user["current_song_artist"]
    song["title"] = user["current_song_title"]
    song["year"] = user["current_song_year"]
    video = user["current_video"]
    score = user["current_score"]


def update_stats():
    # Query database for total guesses and score, update them, then update stats in database
    user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)

    new_total_guesses = user["total_guesses"] + 1
    new_total_score = user["total_score"] + score
    new_average_score = new_total_score / new_total_guesses

    query_db("UPDATE users SET total_guesses = ?, total_score = ?, average_score = ?" " WHERE id = ?", [new_total_guesses, new_total_score, new_average_score, user["id"]])


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    global song
    global video
    global score

    update_current_info()

    cur = get_db().cursor()

    if request.method == "POST":
        # if user is requesting answer:
        if request.form.get("reveal") is not None:
            correct = False
            reveal = True
        # else, user is guessing:
        else:
            # if answer is correct:
            if request.form.get("guess") == song["year"]:
                if score == -1:
                    score = 0
                    update_stats()
                correct = True
                reveal = True
            # if answer is incorrect:
            else:
                if score == -1:
                    score = abs(int(request.form.get("guess")) - int(song["year"]))
                    update_stats()
                correct = False
                reveal = False
        
        # Update current database info
        user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)
        query_db("UPDATE users SET current_correct = ?, current_reveal = ?, current_score = ?" " WHERE id = ?", [correct, reveal, score, user["id"]])
        update_current_info()

        # Calculate current average score:
        average = user["average_score"]

        # Query database for top ten scores for the leaderboard
        leaderboard = query_db("SELECT * FROM users WHERE total_guesses >= 10 ORDER BY average_score LIMIT 10")

        return render_template("index.html", leaderboard=leaderboard, average=average, song=song, video=video, score=score, correct=correct, reveal=reveal)

    else:
        # Query database for random song
        queried_song = query_db("SELECT * FROM songs ORDER BY RANDOM() LIMIT 1")

        song = {
            "artist": queried_song[0]["artist"],
            "title": queried_song[0]["title"],
            "year": queried_song[0]["year"]
        }

        video = search(song["artist"], song["title"])

        score = -1

        # Update user current info
        user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)
        query_db("UPDATE users SET current_song_artist = ?, current_song_title = ?, current_song_year = ?, current_video = ?, current_score = ?" " WHERE id = ?",  [song["artist"], song["title"], song["year"], video, score, user["id"]])

        # Calculate current average score:
        average = user["average_score"]

        # Query database for top ten scores for the leaderboard
        leaderboard = query_db("SELECT * FROM users WHERE total_guesses >= 10 ORDER BY average_score LIMIT 10")

        return render_template("index.html", leaderboard=leaderboard, average=average, song=song, video=video, score=score, reveal=False)


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
        user = query_db("SELECT * FROM users WHERE username = ?", [request.form.get("username")], one=True)

        # Ensure username exists and password is correct
        if user is None or not check_password_hash(user["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user["id"]
        session["username"] = user["username"]

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

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username")

        # Ensure password was submitted
        elif not password:
            return apology("must provide password")

        # Ensure confirmation was submitted
        elif not confirmation:
            return apology("must provide password twice to confirm")

        # Query database for username
        user = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)

        # Ensure username doesn't already exist
        if user is not None:
            return apology("username taken")

        # Ensure password is valid
        if len(password) < 8:
            return apology("password must have 8 or more characters")

        # Ensure password is equal to confirmation
        if password != confirmation:
            return apology("password and password confirmation do not match")

        # Hash password
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Register user
        query_db("INSERT INTO users (username, hash) VALUES (?, ?)", [username, hash])

        # Remember which user has logged in
        user = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

if __name__ == '__main__':
    app.debug = True
    app.run()
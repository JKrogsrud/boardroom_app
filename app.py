from flask import Flask
from flask import render_template
from flask import request
import sqlite3

app = Flask(__name__)

# First load the database
con = sqlite3.connect("python/boardroom.db")
cur = con.cursor()

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/search", methods=['GET','POST'])
def search():
    if request.method == 'GET':
        """
        User has submitted a search of a boardgame.
        First we will search our own database for said game, if not
        found we will search the boardgamegeek API.
        """
        print(request.form["game_title"])
        return render_template('search_result.html', request.form["game_tile"])


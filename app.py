from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
import requests
import xml.etree.ElementTree as ET
import xmltodict
import sqlite3
from markupsafe import escape
from tools import format_description
from tools import search_and_format

"""Some global parameters:"""
# MIN_NUM_VOTES is for measuring whether user polls are worthwhile reporting
MIN_NUM_VOTES = 10

app = Flask(__name__)

# First load the database
con = sqlite3.connect("python/boardroom.db")
cur = con.cursor()

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/search", methods=['GET','POST'])
def search():
    return render_template('search.html')

@app.route("/search_result", methods=['GET', 'POST'])
def search_result():
    # First we look at our own database and see if the game is already part
    # of our database.
    # If it is, return the results of the possible games that meet the search criteria
    # OR create a button that asks us to search boardgamegeek

    # Search BGG
    search_term = request.form['game_title']
    print("Search Term:" + str(search_term))
    game_dict = search_bgg(search_term)
    print("Found games:")
    for game in game_dict:
        print("-" + str(game_dict[game]))
    return render_template('search_result.html', data=game_dict)

def search_bgg(game_title):
    # create the URL to search
    # tag the formatted search term onto the bgg search api
    url = 'https://boardgamegeek.com/xmlapi/search?search=' + str(game_title)
    # send request to bgg API
    response = requests.request("GET", url)
    print("Response Code received from bgg: " + str(response.status_code))
    # result is in XML, convert it to element tree
    # TODO: figure out which other codes ok?
    if response.status_code == 200:
        xml = response.content
        parsed_xml = xmltodict.parse(xml)  # This is a dictionary
        print(parsed_xml)
        bg_search_results = {}  # dictionary {game_id : game_title}
        ## Make sure the list is not empty
        if len(parsed_xml['boardgames']) > 1:
            bg_list = parsed_xml['boardgames']['boardgame']  # This should be a List of dictionaries

            for game in bg_list:
                if type(game['name']) != str:  # Some dictionaries were coming out as strings
                    bg_search_results[game['@objectid']] = game['name']['#text']

            return bg_search_results
        else:
            return None
    else:
        return None

@app.route("/library/add/<gameId>", methods=["GET", "POST"])
def boardgameAdd(gameId):
    # Look up the boardgame by it's unique ID in our database
    # and if not, add it to the database

    # First load the database
    print("Checking if game is already in database..")

    print("Connecting to database..")
    con = sqlite3.connect("python/boardroom.db")
    cur = con.cursor()
    print("Querying boardgames...")

    sql_select_search_boardgames = f"""SELECT * FROM boardgame WHERE id={str(gameId)};"""
    print("result:")
    sql_result = cur.execute(sql_select_search_boardgames).fetchall()
    print(sql_result)

    if len(sql_result) != 1:
        # In this case the game is not part of the database yet so we can add it
        # The boardgame table columns for reference:
        ## id, name, year_published, min_players, max_players, rec_players
        ## min_age, description, image, is_expansion, weight

        api_url = "https://boardgamegeek.com/xmlapi/boardgame/" + str(gameId) + "?stats=1"
        print("Searching for boardgame with id:" + str(gameId))
        response = requests.request(method="GET", url=api_url)
        print("Response received: " + str(response.status_code))

        response_xml = response.content
        response_dict = xmltodict.parse(response_xml)

        game_info = response_dict['boardgames']['boardgame']

        # Find the game name (the primary one)
        if type(game_info['name']) != list:
            # if its not a list just make it a single element list
            names = [game_info['name']]
        else:
            names = game_info['name']
        # Go through each entry and find which one has the '@primary' key
        for name in names:
            try:
                if bool(name['@primary']):
                    game_name = name['#text']
            except:
                pass
        year_published = game_info['yearpublished']
        min_players = game_info['minplayers']
        max_players = game_info['maxplayers']

        ## recommended number of players is the result of a player poll
        ## check the number of votes, anything less than 50 people probably not particularly

        suggested_num_players_poll = game_info['poll'][0]
        # Check that the number of votes is sufficient enough to report
        if int(suggested_num_players_poll['@totalvotes']) > MIN_NUM_VOTES:
            # We pull all votes for the recommended number of votes for each
            all_results = suggested_num_players_poll['results']
            current_max = 0
            rec_players = 0
            for result in all_results:
                num_players = result['@numplayers']
                num_votes = int(result['result'][1]['@numvotes'])
                if num_votes > current_max:
                    current_max = num_votes
                    rec_players = num_players

            if rec_players[-1] == '+':
                rec_players = rec_players[:-1]
            rec_players = int(rec_players)
        else:
            # if not we will report -1 and catch that later
            rec_players = -1

        min_age = game_info['age']
        description = game_info['description']
        image = game_info['image']

        # To check if the game is an expansion or has an expansion check if the dictionary contains 'boardgameexpansion'
        # This value could appear multiple times if it expands multiple games, or has multiple expansions
        # if multiple values exist this will return a list, otherwise a single dictionary

        expansion_to = []
        is_expanded_by = []

        # first we need to check if the key boardgameexpansion exists or not
        if 'boardgameexpansion' in game_info:
            # check if it returned a list
            if type(game_info['boardgameexpansion']) == list:
                # This is the case that we have multiple results
                # We check every entry for a key called '@inbound'
                for expansion in game_info['boardgameexpansion']:
                    try:
                        if bool(expansion['@inbound']):
                            expansion_to.append(expansion['@objectid'])
                    except:
                        # assuming there is no key called '@inbound' we would get an exception
                        # so instead we add the game to is_expanded_by
                        is_expanded_by.append(expansion['@objectid'])
            else:
                # This case we didn't have a list so we don't need to loop
                try:
                    if bool(game_info['boardgameexpansion']['@inbound']):
                        expansion_to.append(game_info['boardgameexpansion']['@objectid'])
                except:
                    is_expanded_by.append(game_info['boardgameexpansion']['@objectid'])

            # We will save this info for later
            if len(expansion_to) > 0:
                is_expansion = 1
            else:
                is_expansion = 0
        # no entry for this means, the game is neither an expansion or is it expanded
        else:
            is_expansion = 0


        # now we get the 'weight'
        weight = game_info['statistics']['ratings']['averageweight']

        # we have all the info we need to start populating our database
        # TODO: Might need to check if there are escape characters in the things entered?
        sql_add = f"""
                    INSERT INTO boardgame (id, name, year_published, min_players, max_players, rec_players, 
                    min_age, description, image, is_expansion, weight)
                    VALUES(
                        {gameId},
                        '{format_description(game_name)}',
                        {year_published},
                        {min_players},
                        {max_players},
                        {rec_players},
                        {min_age},
                        '{format_description(description)}',
                        '{format_description(image)}',
                        {is_expansion},
                        {weight});"""
        print(sql_add)
        cur.execute(sql_add)  # adds it to db

        # add entries to the expansion table if possible
        for base_id in expansion_to:
            if is_expansion == 1:
                # check that the boardgame it expands is in our database already to prevent key errors
                sql_check = f"""SELECT * FROM boardgame WHERE id={base_id};"""
                if len(cur.execute(sql_check).fetchall()) > 0:
                    # game exists so we can add it to the expansion list
                    try:
                        sql_add_expansion = f"""
                                                INSERT INTO expansion (base_id, expansion_id)
                                                VALUES (
                                                        {base_id},
                                                        {gameId});"""
                        cur.execute(sql_add_expansion)
                    except:
                        # It's possible we already added this in case we'd get a UNIQUE constraint integrity error
                        # this is fine and we can move on
                        pass

        # It's possible while going through stock that we might add an expansion before we add the base title
        # in this case when we add the expansion first nothing will be added to the db in this table

        for expansion_id in is_expanded_by:
            sql_check = f"""SELECT * FROM boardgame WHERE id={expansion_id};"""
            sql_result = cur.execute(sql_check).fetchall()
            if len(sql_result) == 0:
                # In this case we can now add a new entry to the expansion table
                print(sql_result)
                sql_add_expansion = f"""
                                        INSERT INTO expansion (base_id, expansion_id)
                                        VALUES (
                                                {gameId},
                                                {expansion_id});"""
                cur.execute(sql_add_expansion)

        # Finally we can go through the game mechanics and add them to the mechanics table
        # try except in case game has no listed mechanics
        # TODO: this isn't working right
        try:
            if type(game_info['boardgamemechanic']) != list:
                mechanic_list = [game_info['boardgamemechanic']]
            else:
                mechanic_list = game_info['boardgamemechanic']

            for mechanic in mechanic_list:
                sql_add_mechanic = f"""
                                        INSERT INTO mechanic (game_id, mechanic)
                                        VALUES (
                                                {gameId},
                                                {mechanic['#text']};"""
                cur.execute(sql_add_mechanic)
        except:
            print("Tried to insert an existing pair..moving on")
    else:
        print(f"Boardgame with id {gameId} already in database...")

    # Commit and Close
    print("Commiting...")
    con.commit()
    print("Closing connection...")
    con.close()
    # game is now added so we redirect to game view
    print("Rendering Template: boardgameAdd.html")
    return render_template('boardgameAdd.html', gameId=gameId)


@app.route("/library/view/<gameId>", methods=["GET", "POST"])
def game_view(gameId):
    ## gameId will have the <> brackets as a string rn
    gameFormat = search_and_format(gameId)
    print("rendering template: boardgameView.html")
    return render_template('boardgameView.html', gameId=gameId)


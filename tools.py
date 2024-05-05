# This function is intended to help insert strings into the SQLite database
# We will add formatting here as needed
import sqlite3

def format_description(desc: str) -> str:
    # replace single quotes with double quotes
    desc = desc.replace("'", "''")
    return desc

def search_and_format(id: int) -> dict:
    # establish a connection with the database
    con = sqlite3.connect("boardroom.db")
    cur = con.cursor()

    # Pull information from boardgame table first
    bg_select = f"""SELECT * FROM boardgame WHERE id={id};"""
    search_result = cur.execute(bg_select).fetchone()

    # as we are searching for an id and that is a primary key
    # the result should return just a single result
    (id, name, year_published, min_players, max_players,
     rec_players, min_age, description, image,
     is_expansion, weight) \
        = search_result[0]

    result_dict = {}
    result_dict['id'] = int(id)
    result_dict['name'] = str(name)
    result_dict['year_published'] = int(year_published)
    result_dict['min_players'] = int(min_players)
    result_dict['max_players'] = int(max_players)
    result_dict['rec_players'] = int(rec_players)
    result_dict['min_age'] = int(min_age)
    result_dict['description'] = str(result_dict)
    result_dict['image'] = str(image)
    result_dict['is_expansion'] = int(is_expansion)
    result_dict['weight'] = float(weight)

    # next we accumulate a list of tags associated with the boardgame





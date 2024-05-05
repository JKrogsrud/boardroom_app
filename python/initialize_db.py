import sqlite3

# First load the database
con = sqlite3.connect("boardroom.db")
cur = con.cursor()

# First create a table for the boardgames
# |__id__|name|year_published|min_players|max_players|recPlayers|age|description|imageUrl|isExpansion|weight

sql_create_bg_table = """
    CREATE TABLE IF NOT EXISTS boardgame (
        id integer PRIMARY KEY,
        name text NOT NULL,
        year_published integer,
        min_players integer,
        max_players integer,
        rec_players integer,
        min_age integer,
        description text,
        image text,
        is_expansion integer,
        weight real
    ); """

cur.execute(sql_create_bg_table)

sql_create_expansion_table = """
    CREATE TABLE IF NOT EXISTS expansion (
        base_id integer,
        expansion_id integer,
        FOREIGN KEY (base_id) REFERENCES boardgame (id),
        FOREIGN KEY (expansion_id) REFERENCES boardgame (id),
        PRIMARY KEY (base_id, expansion_id)
    ); """

cur.execute(sql_create_expansion_table)

sql_create_mechanic_table = """
    CREATE TABLE IF NOT EXISTS mechanic (
        game_id integer,
        mechanic text,
        FOREIGN KEY (game_id) REFERENCES boardgame (id),
        PRIMARY KEY (game_id, mechanic)
    ); """

cur.execute(sql_create_mechanic_table)

con.commit()
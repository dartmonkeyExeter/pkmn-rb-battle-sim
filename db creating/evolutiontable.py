import sqlite3

queries = """

DROP TABLE IF EXISTS evolution;

CREATE TABLE IF NOT EXISTS items (
    Item_ID     INTEGER  NOT NULL UNIQUE PRIMARY KEY,
    Name        TEXT     NOT NULL,
    Description TEXT
);

CREATE TABLE IF NOT EXISTS evolution (
    Pokemon_ID  INTEGER  NOT NULL,
    Evolution_Pokemon_ID  INTEGER  NOT NULL,
    Method      TEXT,
    Level       INTEGER,
    Item_ID     INTEGER,
    PRIMARY KEY (Pokemon_ID, Evolution_Pokemon_ID),
    FOREIGN KEY (Pokemon_ID) REFERENCES pokemon(Number),
    FOREIGN KEY (Evolution_Pokemon_ID) REFERENCES pokemon(Number),
    FOREIGN KEY (Item_ID) REFERENCES items(Item_ID)
);
"""

# Connect to SQLite database
conn = sqlite3.connect('FirstGenPokemon.db')

# Create a cursor object
cursor = conn.cursor()

# Execute the queries
cursor.executescript(queries)

# Commit the changes
conn.commit()

# Close the connection
conn.close()
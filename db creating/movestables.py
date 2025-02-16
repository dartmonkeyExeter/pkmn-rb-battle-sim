import sqlite3
import requests
from bs4 import BeautifulSoup

# Connect to SQLite database
conn = sqlite3.connect('FirstGenPokemon.db')
cursor = conn.cursor()

# Create the tables (if not already created)
queries = """
DROP TABLE IF EXISTS moves;
DROP TABLE IF EXISTS pokemon_moves;

CREATE TABLE IF NOT EXISTS moves (
    Move_ID     INTEGER  NOT NULL UNIQUE PRIMARY KEY,
    Name        TEXT     NOT NULL,
    Type        TEXT     NOT NULL,
    Category    TEXT     NOT NULL,
    Power       INTEGER  NOT NULL,
    Accuracy    INTEGER  NOT NULL,
    PP          INTEGER  NOT NULL,
    Effect      TEXT
);

CREATE TABLE IF NOT EXISTS pokemon_moves (
    Pokemon_Move_ID INTEGER  NOT NULL UNIQUE PRIMARY KEY,
    Pokemon_ID  INTEGER  NOT NULL,
    Move_ID     INTEGER  NOT NULL,
    Level       INTEGER,
    Method      TEXT,
    FOREIGN KEY (Pokemon_ID) REFERENCES pokemon(Number),
    FOREIGN KEY (Move_ID) REFERENCES moves(Move_ID)
);
"""
cursor.executescript(queries)
conn.commit()

# Define the URL to scrape
url = "https://pokemondb.net/move/generation/1"

# Send a GET request to the URL
response = requests.get(url)

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find the table with id="moves"
moves_table = soup.find('table', id='moves')

# Find all the rows in the table
rows = moves_table.find_all('tr')[1:]  # Skip the header row

# Loop through each row and extract the relevant data
for row in rows:
    cols = row.find_all('td')
    if len(cols) == 7:  # Ensure the row has the expected number of columns
        move_name = cols[0].text.strip()
        move_type = cols[1].text.strip().lower()
        category = str(cols[2]).split('alt="')[1].split('"')[0].lower()
        power = cols[3].text.strip()
        accuracy = cols[4].text.strip()
        pp = cols[5].text.strip()
        effect = cols[6].text.strip() if len(cols) > 6 else ''
        
        # Convert power, accuracy, and pp to integers
        try: 
            power = int(power)
        except:
            power = 0
        try:
            accuracy = int(accuracy)
        except:
            accuracy = 0
        try:
            pp = int(pp)
        except:
            pp = 0
            
        # Insert the move into the database
        cursor.execute("""
        INSERT OR REPLACE INTO moves (Name, Type, Category, Power, Accuracy, PP, Effect)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (move_name, move_type, category, power, accuracy, pp, effect))
        conn.commit()

# Close the connection to the database
conn.close()

print("Data scraped and inserted into the database successfully.")

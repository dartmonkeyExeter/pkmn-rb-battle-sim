import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect('FirstGenPokemon.db')

# Read the CSV file
df = pd.read_csv('FirstGenPokemon.csv')

# Create the table in the database
script = """
CREATE TABLE IF NOT EXISTS pokemon (
   Number      INTEGER  NOT NULL UNIQUE PRIMARY KEY,
   Name        TEXT     NOT NULL,
   Type1       TEXT     NOT NULL,
   Type2       TEXT,
   Height_m     REAL     NOT NULL,
   Weight_kg    REAL     NOT NULL,
   Male_Pct    REAL     NOT NULL,
   Female_Pct  REAL     NOT NULL,
   Capt_Rate   INTEGER  NOT NULL,
   Exp_Points  INTEGER  NOT NULL,
   Exp_Speed   TEXT     NOT NULL,
   Base_Total  INTEGER  NOT NULL,
   HP          INTEGER  NOT NULL,
   Attack      INTEGER  NOT NULL,
   Defense     INTEGER  NOT NULL,
   Special     INTEGER  NOT NULL,
   Speed       INTEGER  NOT NULL,
   Legendary   INTEGER  NOT NULL -- Using INTEGER for the BIT field (0 or 1)
);
"""

# Execute the script to create the table
with conn:
    cur = conn.cursor()
    cur.executescript(script)

# Insert the data into the 'pokemon' table
# Select the relevant columns from the DataFrame
columns_to_insert = [
    'Number', 'Name', 'Type1', 'Type2', 'Height_m', 'Weight_kg', 
    'Male_Pct', 'Female_Pct', 'Capt_Rate', 'Exp_Points', 'Exp_Speed',
    'Base_Total', 'HP', 'Attack', 'Defense', 'Special', 'Speed', 'Legendary'
]

print(df.columns)
# Filter the DataFrame to keep only the relevant columns
df_filtered = df.loc[:, columns_to_insert]
# Insert the data into the table
df_filtered.to_sql('pokemon', conn, if_exists='append', index=False)

# Commit and close the connection
conn.commit()
conn.close()

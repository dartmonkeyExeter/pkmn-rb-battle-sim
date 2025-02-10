import sqlite3 

# Connect to the database
conn = sqlite3.connect('FirstGenPokemon.db')
cursor = conn.cursor()

# change high jump kick to Hi Jump Kick
# change Vise Grip to ViceGrip

cursor.execute("UPDATE moves SET Name = 'Hi Jump Kick' WHERE Name = 'High Jump Kick'")
cursor.execute("UPDATE moves SET Name = 'ViceGrip' WHERE Name = 'Vise Grip'")

cursor.close()
conn.commit()

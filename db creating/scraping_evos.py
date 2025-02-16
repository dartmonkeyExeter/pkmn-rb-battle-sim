import sqlite3, re
import requests
from bs4 import BeautifulSoup

# Create a connection to the database
conn = sqlite3.connect('FirstGenPokemon.db')

# Create a cursor object
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS evolution;")
queries = """
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
c.executescript(queries)

for i in range(1,152):
    html = requests.get(f"https://www.serebii.net/pokedex/{i:03}.shtml").text
    soup = BeautifulSoup(html, 'html.parser')
    main_table = soup.find('table', class_="evochain")
    # get all image srcs from main_table
    imgs = main_table.find_all('img')
    if len(imgs) == 1: # to ignore eeveelutions
        print(f"{i} has no evolution line")
        continue
    
    
    order = []
    
    for img in imgs:
        img = str(img)    

        # Check for item evolution
        if 'title="Use ' in img:
            item_parts = img.split('title="Use ')
            if len(item_parts) > 1:
                item = item_parts[1].split('"')[0]
                order.append("Item: " + item)
                continue

        # Check for trade evolution
        if 'title="Trade"' in img:
            order.append("Trade")
            continue

        # Check for level evolution
        if '/pokedex-xy/evoicon/l' in img:
            lvl_parts = img.split('/pokedex-xy/evoicon/l')
            if len(lvl_parts) > 1:
                lvl = lvl_parts[1].split('.png')[0]
                order.append("Level: " + lvl)
                continue

        # Check for Pokémon number
        if '/pokearth/sprites/yellow/' in img:
            poke_parts = img.split('/pokearth/sprites/yellow/')
            if len(poke_parts) > 1:
                pokemon_number = poke_parts[1].split('.png')[0]
                pokemon = c.execute("SELECT Name FROM pokemon WHERE Number = ?", (pokemon_number,)).fetchone()[0]

                if pokemon:
                    order.append("Pokemon: " + pokemon)
                    continue
    
    branch = False
    
    for idx, item in enumerate(order):
        # first, find which position the current mon is, check if there is a mon and method after it
        item = item.split(": ")
        if item[0] == "Pokemon":
            pokemon = item[1]
            no = c.execute("SELECT Number FROM pokemon WHERE Name = ?", (pokemon,)).fetchone()[0]            
            if i == no:
                # if the i is the same number, we've reached it in the order, and need to check the next two
                
                print(f"Checking {pokemon}")
                try:
                    if order[idx + 1].split(": ")[0] == "Pokemon":
                        # brancher (i think)
                        pass
                except:
                    # pokemon has no evos
                    print(f"{i} doesnt evolve")
                    break
                
                if order[idx + 1].split(": ")[0] == "Item" and order[idx + 2].split(": ")[0] == "Item":
                    branch = True
                
                if order[idx + 1].split(": ")[0] == "Item" and order[idx + 2].split(": ")[0] == "Pokemon":
                    # pokemon evolves with given item into next pokemon
                    item = order[idx + 1].split(": ")[1]
                    item_id = c.execute("SELECT Item_ID FROM items WHERE REPLACE(UPPER(Name), ' ', '') = ?", (str(item).upper().replace(" ", ""),)).fetchone()[0]
                    next_pokemon = order[idx + 2].split(": ")[1]
                    next_no = c.execute("SELECT Number FROM pokemon WHERE Name = ?", (next_pokemon,)).fetchone()[0]
                    print(f"{pokemon} evolves into {next_pokemon} with {item}")
                    c.execute("INSERT INTO evolution (Pokemon_ID, Evolution_Pokemon_ID, Method, Item_id) VALUES (?, ?, ?, ?)", (no, next_no, f"ITEM", item_id))
                    
                if order[idx + 1].split(": ")[0] == "Trade" and order[idx + 2].split(": ")[0] == "Pokemon":
                    # pokemon evolves by trade into next pokemon
                    next_pokemon = order[idx + 2].split(": ")[1]
                    next_no = c.execute("SELECT Number FROM pokemon WHERE Name = ?", (next_pokemon,)).fetchone()[0]
                    print(f"{pokemon} evolves into {next_pokemon} by trade")
                    c.execute("INSERT INTO evolution (Pokemon_ID, Evolution_Pokemon_ID, Method) VALUES (?, ?, ?)", (no, next_no, "TRADE"))
                    
                if order[idx + 1].split(": ")[0] == "Level" and order[idx + 2].split(": ")[0] == "Pokemon":
                    # pokemon evolves by level into next pokemon
                    lvl = order[idx + 1].split(": ")[1]
                    next_pokemon = order[idx + 2].split(": ")[1]
                    next_no = c.execute("SELECT Number FROM pokemon WHERE Name = ?", (next_pokemon,)).fetchone()[0]
                    print(f"{pokemon} evolves into {next_pokemon} at level {lvl}")
                    c.execute("INSERT INTO evolution (Pokemon_ID, Evolution_Pokemon_ID, Method, Level) VALUES (?, ?, ?, ?)", (no, next_no, "LVL", lvl))
                
                break # we've found the pokemon, no need to continue
            
    if branch:
        # find amount of items in order
        # remove the current and prescending pokemon from the order
        
        print("Branching evolution")
        
        new_order = []
        
        hit_current = False
        
        for item in order:
            # only start appending AFTER reaching current pokemon
            if item.split(": ")[1] == pokemon:
                hit_current = True
                continue
            
            if hit_current:
                new_order.append(item)
                
        items = []
        branch_mons = []
        
        for item in new_order:
            if item.split(": ")[0] == "Item":
                items.append(item.split(": ")[1])
            if item.split(": ")[0] == "Pokemon":
                branch_mons.append(item.split(": ")[1])
                
        # now each item has the same index as the pokemon it evolves into
        for idx, item in enumerate(items):
            next_pokemon = branch_mons[idx]
            next_no = c.execute("SELECT Number FROM pokemon WHERE Name = ?", (next_pokemon,)).fetchone()[0]
            item_id = c.execute("SELECT Item_ID FROM items WHERE REPLACE(UPPER(Name), ' ', '') = ?", (str(item).upper().replace(" ", ""),)).fetchone()[0]
            print(f"{pokemon} evolves into {next_pokemon} with {item}")
            c.execute("INSERT INTO evolution (Pokemon_ID, Evolution_Pokemon_ID, Method, Item_ID) VALUES (?, ?, ?, ?)", (no, next_no, f"ITEM", item_id))
            
conn.commit()
conn.close()
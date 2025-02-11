import sqlite3, requests
from bs4 import BeautifulSoup

conn = sqlite3.connect('FirstGenPokemon.db')
things_to_find = ["Moves learnt by level up", "Moves learnt by TM", "Moves learnt by HM"]
cursor = conn.cursor()

# Clear table before beginning
cursor.execute("DELETE FROM pokemon_moves")

edgecases = {
    "mr. mime": "mr-mime",
    "nidoran♀": "nidoran-f",
    "nidoran♂": "nidoran-m",
    "farfetch'd": "farfetchd",
}

for i in range(1, 152):
    pokename = cursor.execute(f"SELECT Name FROM pokemon WHERE Number = {i}").fetchone()[0].lower()
    
    if pokename in edgecases.keys():
        pokename = edgecases[pokename]
    
    url = f"https://pokemondb.net/pokedex/{pokename.lower()}/moves/1"
    
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check response status
    if response.status_code != 200:
        print(f"Failed to retrieve {url}: {response.status_code}")
        continue
    
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the div holding each thing in things_to_find
    for idx, thing in enumerate(things_to_find):
        found = soup.find('h3', string=thing)
        if not found:
            print(f"Could not find {thing} in {pokename}")
            continue
        
        table_div = found.find_next_sibling('div', class_='resp-scroll')
        try:
            table = table_div.find('table')
            if not table:
                print(f"No table found for {thing} on {pokename}")
                continue
        except:
            continue
        
        # Process the table based on the index
        if idx == 0 and str(table.find_all('tr')[0].text).split(" ")[0] == "Lv.":
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                level = cols[0].text
                move = cols[1].text
                try:
                    move_id = cursor.execute(f"SELECT Move_ID FROM moves WHERE REPLACE(REPLACE(LOWER(Name), ' ', ''), '-', '') = REPLACE(REPLACE(LOWER(?), ' ', ''), '-', '')", (move,)).fetchone()[0]

                    cursor.execute("INSERT INTO pokemon_moves (Pokemon_ID, Move_ID, Level, Method) VALUES (?, ?, ?, ?)", (i, move_id, level, "LEVEL"))
                except sqlite3.IntegrityError:
                    print("this shouldnt happen anymore")
                    continue
                except TypeError:
                    print(f"NONE TYPE ERROR: {move}")
                    print(url)
                    continue
                except Exception as e:
                    print(f"Error processing level-up move: {move}")
                    print(e)
                    print(url)
                    continue
                
        elif idx == 1 and str(table.find_all('tr')[0].text).split(" ")[0] == "TM":
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                move = cols[1].text
                try:
                    move_id = cursor.execute(f"SELECT Move_ID FROM moves WHERE REPLACE(REPLACE(LOWER(Name), ' ', ''), '-', '') = REPLACE(REPLACE(LOWER(?), ' ', ''), '-', '')", (move,)).fetchone()[0]

                    cursor.execute("INSERT INTO pokemon_moves (Pokemon_ID, Move_ID, Method) VALUES (?, ?, ?)", (i, move_id, "TM"))
                except sqlite3.IntegrityError:
                    print("this shouldnt happen anymore")
                    continue
                except TypeError:
                    print(f"NONE TYPE ERROR: {move}")
                    print(url)
                    continue
                except Exception as e:
                    print(f"Error processing level-up move: {move}")
                    print(e)
                    print(url)
                    continue
                
        elif idx == 2 and str(table.find_all('tr')[0].text).split(" ")[0] == "HM":
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                move = cols[1].text
                try:
                    move_id = cursor.execute(f"SELECT Move_ID FROM moves WHERE REPLACE(REPLACE(LOWER(Name), ' ', ''), '-', '') = REPLACE(REPLACE(LOWER(?), ' ', ''), '-', '')", (move,)).fetchone()[0]

                    cursor.execute("INSERT INTO pokemon_moves (Pokemon_ID, Move_ID, Method) VALUES (?, ?, ?)", (i, move_id, "HM"))
                except sqlite3.IntegrityError:
                    print("this shouldnt happen anymore")
                    continue
                except TypeError:
                    print(f"NONE TYPE ERROR: {move}")
                    print(url)
                    continue
                except Exception as e:
                    print(f"Error processing level-up move: {move}")
                    print(e)
                    print(url)
                    continue
                
        
        conn.commit()

conn.close()

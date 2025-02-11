import sqlite3, re
import requests
from bs4 import BeautifulSoup

# Create a connection to the database
conn = sqlite3.connect('FirstGenPokemon.db')

# Create a cursor object
c = conn.cursor()


for i in range(1,152):
    html = requests.get(f"https://www.serebii.net/pokedex/{i:03}.shtml").text
    soup = BeautifulSoup(html, 'html.parser')
    main_table = soup.find('table', class_="evochain")
    # get all image srcs from main_table
    imgs = main_table.find_all('img')
    if len(imgs) == 1:
        print(f"{i} has no evolutions")
        continue
    
    items = []
    
    for img in imgs:
        # first we need to check if multiple items come after each other, indicating a branched evolution
        
        img = str(img)
        
        try:
            item = img.split('title="Use ')[1].split('"')[0]
        except:
            pass
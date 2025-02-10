import sqlite3, re
import requests
from bs4 import BeautifulSoup

# Create a connection to the database
conn = sqlite3.connect('FirstGenPokemon.db')

# Create a cursor object
c = conn.cursor()

def parse_pokemon_evolutions(html_snippets):
    evolution_data = {}
    
    for html in html_snippets:
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all('img')
        links = soup.find_all('a', href=True)
        
        dex_numbers = [
            int(link['href'].split('/')[-1].split('.')[0])
            for link in links if 'pokedex' in link['href']
        ]
        
        evo_conditions = [img['title'].strip() for img in images if 'title' in img.attrs]
        
        if len(dex_numbers) == 1:
            evolution_data[dex_numbers[0]] = {}
        else:
            evolution_data[dex_numbers[0]] = {}
            for i in range(1, len(dex_numbers)):
                condition = evo_conditions[i - 1] if i - 1 < len(evo_conditions) else "Unknown"
                evolution_data[dex_numbers[0]][dex_numbers[i]] = condition
    
    return evolution_data

url = "https://www.serebii.net/pokedex/001.shtml"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
evolution_tables = soup.find_all('tbody')
print(evolution_tables)
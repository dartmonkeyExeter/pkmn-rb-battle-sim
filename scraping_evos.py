import sqlite3, re
import requests
from bs4 import BeautifulSoup

# Create a connection to the database
conn = sqlite3.connect('FirstGenPokemon.db')

# Create a cursor object
c = conn.cursor()

html = requests.get("https://www.serebii.net/pokedex/001.shtml").text
soup = BeautifulSoup(html, 'html.parser')
main_table = soup.find('table', class_="evochain")
# get all image srcs from main_table
imgs = main_table.find_all('img')
print(imgs)
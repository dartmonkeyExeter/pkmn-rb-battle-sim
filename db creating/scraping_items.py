import sqlite3, requests
from bs4 import BeautifulSoup

conn = sqlite3.connect('FirstGenPokemon.db')
cursor = conn.cursor()

# Clear table before beginning
cursor.execute("DROP TABLE IF EXISTS items")
cursor.execute("CREATE TABLE items (Item_ID INTEGER NOT NULL UNIQUE PRIMARY KEY, Name TEXT NOT NULL, Description TEXT, Found TEXT, Price INTEGER)")

url = "https://www.serebii.net/rb/items.shtml"

response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find('table', class_='dextable')

for row in table.find_all('tr')[1:]:
    cols = row.find_all('td')
    name = cols[0].text
    description = cols[1].text
    found = cols[2].text
    price = cols[3].text
    
    cursor.execute("INSERT INTO items (Name, Description, Found, Price) VALUES (?, ?, ?, ?)", (name, description, found, price))
    
conn.commit()
conn.close()
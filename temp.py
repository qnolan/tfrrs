import csv
import requests
from bs4 import BeautifulSoup
import re
 
 
url="https://www.tfrrs.org/athletes/7722962/Oregon/Micah_Williams"
r=requests.get(url)
soup=BeautifulSoup(r.content,"lxml")

events = []

rs = []
for r in soup.find_all('h3'):
    rs.append(r.text.strip())

print(rs) 

tables = soup.find_all('table')
 
print(f"[+] Found a total ddd of {len(tables)} tables.")
 

for i, table in enumerate(tables, start=1):

    # get all the rows of the table
    #rows = get_table_rows(table)
    # save table as csv file
    hs = []
    

    for h in table.find_all('thead'):
        for tr in h.find_all('tr'):

            hs.append(re.sub('[\n\t\r↑]', '', h.text.strip().replace('Top', '')))
    print(hs)
    if i == 5:
        break
    

def get_table_rows(table):
    """Given a table, returns all its rows"""

    global i
    i += 1
    if i == 1:
        print(table)
        i += 1

    rows = []
    for tr in table.find_all("tr"):
        cells = []
        # grab all td tags in this table row
        tds = tr.find_all("td")
        if len(tds) == 0:
            # if no td tags, search for th tags
            # can be found especially in wikipedia tables below the table
            ths = tr.find_all("th")
            for i in range(len(ths)):
                cells.append(ths[i].text.strip())
        else:
            # use regular td tags
            for i in range(len(tds)):
                cells.append(tds[i].text.strip())
        rows.append(cells)
    return rows

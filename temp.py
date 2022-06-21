import csv
import requests
from bs4 import BeautifulSoup
 
 
url="https://www.tfrrs.org/lists/3492.html?limit=5&event_type=all&year=&gender=m"
r=requests.get(url)
soup=BeautifulSoup(r.content,"lxml")
 
table = soup.find('table')
 
 #https://medium.com/geekculture/web-scraping-tables-in-python-using-beautiful-soup-8bbc31c5803e
with open('a.csv', 'w+', newline='') as f:
    writer = csv.writer(f)
    for tr in table.find_all('tr'):
        row = [t for t in tr(['td', 'th'])]
        #writer.writerow(row)

        cols = tr.find_all('td')

        # athlete link = href[1]
        href = [t['href'] for t in tr(['a'])]

        if cols != []:
            writer.writerow([cols[1].find('a')['href']])
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import os
import datetime
import re
import uuid

school_ids = {}

indoor_lists = [3492,3157,2770,2324,2124,1797,1569,1345,1139,942,769,607,502]
outdoor_lists = [3711,3191,2909,2279,1912,1688,1439,1228,1029,840,673]

indoor_events = ["60 Meters", "200 Meters", "400 Meters", "800 Meters", "Mile", "3000 Meters", "5000 Meters", "60 Hurdles"]
outoor_events = ["100 Meters", "200 Meters", "400 Meters", "800 Meters", "1500 Meters", "5000 Meters", "110 Hurdles", "400 Hurdles", "3000 Steeplechase"]

indoor_headers = ["PLACE", "ATHLETE", "URL", "TEAM", "MEET", "DATE", "ATHLETE_ID", "SCHOOL_ID", "YEAR", "EVENT", "TIME"]
outdoor_headers = ["PLACE", "ATHLETE", "URL", "TEAM", "MEET", "DATE", "ATHLETE_ID", "SCHOOL_ID", "YEAR", "WIND", "EVENT", "TIME"]

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
# US english
LANGUAGE = "en-US,en;q=0.5"

def get_soup(url):
    """Constructs and returns a soup using the HTML content of `url` passed"""
    # initialize a session
    session = requests.Session()
    # set the User-Agent as a regular browser
    session.headers['User-Agent'] = USER_AGENT
    # request for english content (optional)
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    # make the request
    html = session.get(url)
    # return the soup
    return bs(html.content, "html.parser")

def get_all_tables(soup):
    """Extracts and returns all tables in a soup object"""
    return soup.find_all("table")

def get_table_headers(table):
    """Given a table soup, returns all the headers"""
    headers = []
    for th in table.find("tr").find_all("th"):
        headers.append(th.text.strip())
    return headers


j = 0

def get_table_rows(table, event, indoor):
    """Given a table, returns all its rows"""

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = []
        # grab all td tags in this table row
        tds = tr.find_all("td")
        if len(tds) == 0:
            # if no td tags, search for th tags
            # can be found especially in wikipedia tables below the table
            ths = tr.find_all("th")
            for i in range(len(ths)):
                cells.append(ths[i].text.strip())
                # get athlete link
                if i == 1:
                    cells.append(ths[i].find('a')['href'])
        else:
            # use regular td tags
            for i in range(len(tds)):
                cells.append(tds[i].text.strip())
                # get athlete link
                if i == 1:
                    cells.append(tds[i].find('a')['href'])
        if event != "None":
            cells = format_row(cells, event, indoor)
        rows.append(cells)
    return rows

def get_athlete_id(link):
    temp = link[link.index('athletes/') + len('athletes/'):]
    return temp[:temp.index('/')]

# convert times to seconds (ex: '1:14.27' -> '74.27')
def format_time(time):
    # strip non numeric chars and split into an arry by ':' and '.'
    times = list(map(int, re.split('[.:]', re.sub('[^\d:.]+', '', time))))
    # convert time to seconds
    sec = 0
    length = len(times)
    # HH:MM:SS.mm
    if length == 4:
        sec = times[0] * 3600 + times[1] * 60 + times[2] + times[3] / 100
    # MM:SS.mm
    elif length == 3:
        sec = times[0] * 60 + times[1] + times[2] / 100
    # SS.mm
    else:
        sec = times[0] + times[1] / 100
    return sec

def get_school_id(school):

    if school.upper() == 'Unattached'.upper():
        return '-1'

    if school.upper() not in school_ids:
        school_ids[school.upper()] = str(uuid.uuid4().int)
    return school_ids[school.upper()]

def format_grade(grade):
    return {'FR-1': '1', 'SO-2': '2', 'JR-3': '3', 'SR-4': '4', '': ''}[grade]

# convert dates (ex: 'Jan 14, 2022' -> '01/14/2022')
def format_date(date):
    split_date  = re.split('\W+', date)
    return '{:02d}'.format(datetime.datetime.strptime(split_date[0],'%b').month) + '/' + split_date[1] + '/' + split_date[2]


def format_row(row, event, indoor):

    row[3] = format_grade(row[3])
    row[5] = format_time(row[5])
    row[7] = format_date(row[7])

    # returna and rearrange columns as: rank, name, url, school, meet, date, name id, school id, grade, [wind (or 0),] event, time
    return [row[0], row[1], row[2], row[4], row[6], row[7], get_athlete_id(row[2]), get_school_id(row[4]), row[3], event, row[5]] if indoor else [row[0], row[1], row[2], row[4], row[6], row[7], get_athlete_id(row[2]), get_school_id(row[4]), row[3], row[8] if len(row) == 9 else '0.0', event, row[5]]


#change so fie is delted adn recreatde if exists and add header to top
def save_as_csv(rows, filename):
    pd.DataFrame(rows).to_csv(filename, mode='a+', header=False, index=False)

def processURL(url, event_list, indoor, filename):
    # get the soup
    soup = get_soup(url)
    # extract all the tables from the web page
    tables = get_all_tables(soup)
    print(f"[+] Found a total of {len(tables)} tables.")

    # iterate over all tables
    count = 0
    for i, table in enumerate(tables, start=1):

        # outdoor skips
        if not indoor and i != 1 and i !=3 and i != 5 and i != 7 and i != 9 and i != 11 and i != 16 and i != 17 and i != 19:
            continue
        # indoor skips
        if indoor and (i % 2 == 0 or i > 15):
            continue
       
        # get all the rows of the table
        rows = get_table_rows(table, event_list[count], indoor)
        # save table as csv file
        table_name = f"table-{count}"
        print(f"[+] Saving {table_name}")
        save_as_csv(rows, filename)
        count += 1


def get_data(indoor):

    # get what season we are doing and clear the file if it exists
    szn = "indoor" if indoor else "outdoor"
    szn_list = indoor_lists if indoor else outdoor_lists
    szn_events = indoor_events if indoor else outoor_events
    filename = f"master_{szn}.csv"
    if os.path.exists(filename):
        os.remove(filename)

    i = 0
    for lst in szn_list:
        processURL(f"https://www.tfrrs.org/lists/{lst}.html?limit=500&event_type=all&year=&gender=", szn_events, indoor, filename)

    return 0


#get_data(False)

processURL("https://www.tfrrs.org/lists/3492.html?limit=500&event_type=all&year=&gender=m", indoor_events, True, "indoor_2022.csv")

#processURL("https://www.tfrrs.org/lists/3711.html?limit=500&event_type=all&year=&gender=m", outoor_events, False, "outdoor_2022.csv")


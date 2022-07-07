from bs4 import BeautifulSoup as bs
import pandas as pd
import re, csv, datetime, requests, uuid

# track school names mapped to school IDs
school_ids = {}

# read in school IDs we have so far
def read_school_ids():
    with open('data/school_ids.csv', 'r') as f:
        reader = csv.reader(f)
        for line in reader:
            school_ids[line[0]] = line[1]

read_school_ids()

# saves the school_ids we have so far
def save_school_ids():
    with open('data/school_ids.csv', 'w+') as f:
        writer = csv.writer(f)
        for k in school_ids:
            writer.writerow([k, school_ids[k]])


# get the school ID that matches the given name
def get_school_id(school):

    if school.upper() == 'Unattached'.upper():
        return '-1'

    if school.upper() not in school_ids:
        school_ids[school.upper()] = str(uuid.uuid4().int)
    return school_ids[school.upper()]

# Constructs and returns a soup using the HTML content of url passed
def get_soup(url):
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"

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

# Given a table soup, returns all the headers
def get_table_headers(table):
    headers = []
    for th in table.find("tr").find_all("th"):
        headers.append(th.text.strip())
    return headers

# converts grade to numeric format
def format_grade(grade):
    grades = {'FR-1': '1', 'SO-2': '2', 'JR-3': '3', 'SR-4': '4', '': ''}
    if grade not in grades:
        return ''
    return grades[grade]

# convert dates (ex: 'Jan 14, 2022' -> '01/14/2022')
def format_date(date):
    split_date  = re.split('\W+', date)
    return '{:02d}'.format(datetime.datetime.strptime(split_date[0],'%b').month) + '/' + split_date[1] + '/' + split_date[2]

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

# strips the ahtlete ID from link
def get_athlete_id(link):
    temp = link[link.index('athletes/') + len('athletes/'):]
    return temp[:temp.index('/')]


#change so fie is delted adn recreatde if exists and add header to top
def save_as_csv(rows, filename):
    pd.DataFrame(rows).to_csv(filename, mode='a+', header=False, index=False)

def clean_text(txt):
    return re.sub('[\n\t\r↑]', '', txt.text.strip().replace('Top', ''))

from re import T
import tfrrs_master as master
import csv
import re
import os

athletes = []


indoor_events = ["60 Meters (Indoor)", "200 Meters (Indoor)", "400 Meters (Indoor)", "800 Meters (Indoor)", "Mile (Indoor)", "3000 Meters (Indoor)", "5000 Meters (Indoor)", "60 Hurdles (Indoor)"]
outoor_events = ["100 Meters (Outdoor)", "200 Meters (Outdoor)", "400 Meters (Outdoor)", "800 Meters (Outdoor)", "1500 Meters (Outdoor)", "5000 Meters (Outdoor)", "110 Hurdles (Outdoor)", "400 Hurdles (Outdoor)", "3000 Steeplechase (Outdoor)"]

imap = {i: False for i in indoor_events}
omap = {o: False for o in outoor_events}

i = 0

def clean_text(txt):
    return re.sub('[\n\t\r↑]', '', txt.text.strip().replace('Top', ''))


def format_row(row, event, indoor, athlete):

    name_id = athlete[6]
    grade = athlete[8]
    time = row[0]
    wind = '0.0'
    school = athlete[3]
    school_id = master.get_school_id(school)

    # remove prev school from time cell
    if '*' in time:
        school = time[time.index('*') + 5:]
        school_id = master.get_school_id(school)
        time = time[:time.index('*')]

    # remove wind from time cell
    if bool(re.search('[^\d.:]', time)):
        if '(' in time and ')' in time and not indoor:
            wind = time[time.index('(') + 1 : time.index(')')]
            time = time[:time.index('(')]
        if 'w' in time:
            time = time.replace('w', '')

    # convert to seconds if not FS, DQ, DNF, ...
    if not bool(re.search('[^\d.:]', time)):
        time = master.format_time(time)

    #date = master.format_date(row[2])
    date = row[2]

    return [athlete[1], school, row[1], date, name_id, school_id, grade, event, time] if indoor else [athlete[1], school, row[1], date, name_id, school_id, grade, wind, event, time]

def save_table_rows(table, athlete):
    """Given a table, returns all its rows"""

    rows = []
    filename = ''

    # get the table header
    for thead in table.find_all('thead'):
        h = clean_text(thead)

        # check that we are seeing this header for the first time
        # (we don't want to process the 'Progression' tab)
        process = False
        indoor = True
        event = h
        if h in omap and omap[h] == False:
            indoor = False
            omap[h] = True
            process = True
            filename = 'athletes_outdoor.csv'
        elif h in imap and imap[h] == False:
            imap[h] = True
            process = True
            filename = 'athletes_indoor.csv'
        
        if process:

            # remove the (Outdoor)/(Indoor) from h
            event = event[:event.index('(') - 1]

            for tr in table.find_all('tr'):
                cells = []
                # grab all td tags in this table row
                tds = tr.find_all("td")
                if len(tds) == 0:
                    # if no td tags, search for th tags
                    # can be found especially in wikipedia tables below the table
                    ths = tr.find_all("th")
                    for i in range(len(ths)):
                        cells.append(clean_text(ths[i]))
                else:
                    # use regular td tags
                    for i in range(len(tds)):
                        cells.append(clean_text(tds[i]))
                # skip table headers
                if len(cells) > 1:
                    cells = format_row(cells, event, indoor, athlete)
                    rows.append(cells)
    
    if rows != [] and filename != '':
        master.save_as_csv(rows, filename)

def process_file(filename):
    with open(filename) as file:
        reader = csv.reader(file)
        for line in reader:
            global imap, omap
            imap = {i: False for i in indoor_events}
            omap = {o: False for o in outoor_events}
            get_athlete_data(line)

# "https://www.tfrrs.org/athletes/7722962/Oregon/Micah_Williams"
def get_athlete_data(athlete):

    # if we have not processed this athlete ID yet
    if athlete[6] not in athletes:
        athletes.append(athlete[6])
    
        #print(athlete[1])
        
        '''url = 'https://www.tfrrs.org/athletes/8012266/Florida/Jacory_Patterson'
        #url = 'https://www.tfrrs.org/athletes/6905268/Michigan/Devin_Meyrer'
        #url = 'https://www.tfrrs.org/athletes/7722962/Oregon/Micah_Williams'
        '''

        # get the soup
        soup = master.get_soup('https:' + athlete[2])

        # extract all the tables from the web page
        tables = soup.find_all('table')
        print(f"[x] Found a total of {len(tables)} tables.")

        # iterate over all tables
        for i, table in enumerate(tables, start=1):
            # get all the rows of the table
            save_table_rows(table, athlete)

    return 0


if os.path.exists('athletes_outdoor.csv'):
    os.remove('athletes_outdoor.csv')
if os.path.exists('athletes_indoor.csv'):
    os.remove('athletes_indoor.csv')

process_file('indoor_2022.csv')



print(f'[+] Found {len(athletes)} athletes')













''' 
Cases to consider for names:
    'Heath Jr., Rodney'         -> 'Rodney_HeathJr'
    'Carr Jr, Andre'            -> 'Andre_CarrJr'
    'Croom-McFadden, Malcolm'   -> 'Malcolm_CroomMcFadden'
    'Davis II, Shakorie'        -> 'Shakorie_DavisII'
    'Horton, Jon'Terio'         -> 'JonTerio_Horton'

Cases to consider for schools:
    'N. Carolina A&T'       -> 'N_Carolina_AT'
    'Arkansas-Little Rock'  -> 'ArkansasLittle_Rock'
    'Mount St. Mary's'      -> 'Mount_St_Marys'
    'Loyola (Ill.)'         -> 'Loyola_Ill'
    'Texas A&M-CC'          -> 'Texas_AMCC'

'''
import tfrrs_master as master
import csv
import re
import os
from threading import Thread, Lock
import multiprocessing

NUM_CPUS = multiprocessing.cpu_count()
#NUM_CPUS = 32

print('Number of CPUs: ', NUM_CPUS)

mutex = Lock()

indoor_events = ["60 Meters (Indoor)", "200 Meters (Indoor)", "400 Meters (Indoor)", "800 Meters (Indoor)", "Mile (Indoor)", "3000 Meters (Indoor)", "5000 Meters (Indoor)", "60 Hurdles (Indoor)"]
outoor_events = ["100 Meters (Outdoor)", "200 Meters (Outdoor)", "400 Meters (Outdoor)", "800 Meters (Outdoor)", "1500 Meters (Outdoor)", "5000 Meters (Outdoor)", "110 Hurdles (Outdoor)", "400 Hurdles (Outdoor)", "3000 Steeplechase (Outdoor)"]

def clean_text(txt):
    return re.sub('[\n\t\r↑]', '', txt.text.strip().replace('Top', ''))


def format_row(row, event, indoor, athlete):

    name_id = athlete[6]
    grade = '' if athlete[8] == '' else int(athlete[8])
    time = row[0]
    date = row[2]
    wind = '0.0'
    school = athlete[3]
    school_id = master.get_school_id(school)
    record_year = int(athlete[5][athlete[5].rindex('/') + 1:])

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

    # takes care of 'Mmm dd-dd, yyyy' format
    if '-' in date and ',' in date:
        date = date.replace(' - ', '-')
        date = date[:date.index('-')] + date[date.index(','):]
    # converts from 'Mmm dd, yyyy' to 'mm/dd/yyyy'
    if ',' in date:
        date = master.format_date(date)
    # takes care of '(mm/dd- mm/dd)' -> 'mm/dd/yyyy'
    if '(' in date and ')' in date:
        date = date[1:len(date) - 1]
        if '-' in date:
            date = date.replace(' - ', '-')
            date = date.replace('- ', '-')
            date = date[:date.index('-')] + '/' + str(record_year)
            if len(date[:date.index('/')]) == 1:
                date = '0' + date

    if grade != '':
        # find what year this athlete was for this race
        race_year = int(date[date.rindex('/') + 1:])
        race_month = int(date[:date.index('/')])
        record_month = int(athlete[5][:athlete[5].index('/')])

        # increment the year if a race happened in Nov/Dec
        if race_month == 11 or race_month == 12:
            race_year += 1
        if record_month == 11 or record_month == 12:
            record_year += 1

        if race_year != record_year:
            grade -= record_year - race_year
            grade = 1 if grade < 1 else grade
            grade = 4 if grade > 4 else grade

    return [athlete[1], school, row[1], date, name_id, school_id, str(grade), event, time] if indoor else [athlete[1], school, row[1], date, name_id, school_id, str(grade), wind, event, time]

def save_table_rows(table, athlete, imap, omap):
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
            #print('Event:', event)
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
        mutex.acquire()
        print(f'[x] processed {len(rows)} entries')
        master.save_as_csv(rows, filename)   
        mutex.release()

# "https://www.tfrrs.org/athletes/7722962/Oregon/Micah_Williams"
def get_athlete_data(entries, athletes, ct):

    for athlete in entries:

        # if we have not processed this athlete ID yet
        mutex.acquire()
        if athlete[6] not in athletes:
            athletes[ct] = athlete[6]
            mutex.release()
            ct += 1        
        
            # get the soup
            soup = master.get_soup('https:' + athlete[2])

            # extract all the tables from the web page
            tables = soup.find_all('table')
            '''mutex.acquire()
            print(f"[x] Found a total of {len(tables)} tables.")
            mutex.release()'''


            imap = {i: False for i in indoor_events}
            omap = {o: False for o in outoor_events}

            # iterate over all tables
            for i, table in enumerate(tables, start=1):
                # get all the rows of the table
                save_table_rows(table, athlete, imap, omap)
        else:
            mutex.release()
    return 0

def process_file(filename, athletes):
    with open(filename) as file:
        lines = list(csv.reader(file))
        t_len = len(lines) // NUM_CPUS

        ts = [None] * NUM_CPUS
        ct = len(athletes)
        athletes += [''] * len(lines)

        for i in range(NUM_CPUS):
            if i == NUM_CPUS - 1:
                ts[i] = Thread(target=get_athlete_data, args=[lines[t_len * i:], athletes, ct])
            else:
                ts[i] = Thread(target=get_athlete_data, args=[lines[t_len * i:t_len* (i + 1)], athletes, ct])
                ct += t_len
            ts[i].start()
        
        # join al threads
        for i in range(NUM_CPUS):
            ts[i].join()

        return 0

if os.path.exists('athletes_outdoor.csv'):
    os.remove('athletes_outdoor.csv')
if os.path.exists('athletes_indoor.csv'):
    os.remove('athletes_indoor.csv')

print(len(master.school_ids))

athletes = []

#process_file('test.csv', athletes)
process_file('master_indoor.csv', athletes)
process_file('master_outdoor.csv', athletes)

with open('school_ids.csv', 'w+') as f:
    writer = csv.writer(f)
    for k in master.school_ids:
        writer.writerow([k, master.school_ids[k]])

#process_file('master_indoor.csv')


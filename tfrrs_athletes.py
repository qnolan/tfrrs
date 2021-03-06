import tfrrs_util as util
from threading import Thread, Lock
import csv, re, os, multiprocessing

NUM_CPUS = multiprocessing.cpu_count()
#NUM_CPUS = 32
print('Number of CPUs: ', NUM_CPUS)

mutex = Lock()
indoor_events = ["60 Meters (Indoor)", "200 Meters (Indoor)", "400 Meters (Indoor)", "800 Meters (Indoor)", "Mile (Indoor)", "3000 Meters (Indoor)", "5000 Meters (Indoor)", "60 Hurdles (Indoor)"]
outoor_events = ["100 Meters (Outdoor)", "200 Meters (Outdoor)", "400 Meters (Outdoor)", "800 Meters (Outdoor)", "1500 Meters (Outdoor)", "5000 Meters (Outdoor)", "110 Hurdles (Outdoor)", "400 Hurdles (Outdoor)", "3000 Steeplechase (Outdoor)"]

# formats the given row to what we want
def format_row(row, event, indoor, athlete):

    name_id = athlete[6]
    grade = '' if athlete[8] == '' else int(athlete[8])
    time = row[0]
    date = row[2]
    wind = '0.0'
    school = athlete[3]
    school_id = util.get_school_id(school)
    record_year = int(athlete[5][athlete[5].rindex('/') + 1:])

    # remove prev school from time cell
    if '*' in time:
        school = time[time.index('*') + 5:]
        school_id = util.get_school_id(school)
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
        time = util.format_time(time)

    # takes care of 'Mmm dd-dd, yyyy' format
    if '-' in date and ',' in date:
        date = date.replace(' - ', '-')
        date = date[:date.index('-')] + date[date.index(','):]
    # converts from 'Mmm dd, yyyy' to 'mm/dd/yyyy'
    if ',' in date:
        date = util.format_date(date)
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

        # adjust grade accordingly
        if race_year != record_year:
            grade -= record_year - race_year
            grade = 1 if grade < 1 else grade
            grade = 4 if grade > 4 else grade

    # format the same as the master file but no rank
    return [athlete[1], school, row[1], date, name_id, school_id, str(grade), event, time] if indoor else [athlete[1], school, row[1], date, name_id, school_id, str(grade), wind, event, time]

# saves the table rows to a csv after they have been formatted
def save_table_rows(table, athlete, imap, omap):
    rows = []
    filename = ''

    # get the table header
    for thead in table.find_all('thead'):
        h = util.clean_text(thead)

        # check that we are seeing this header for the first time
        # (we don't want to process the 'Progression' tab)
        process = False
        indoor = True
        event = h
        if h in omap and omap[h] == False:
            indoor = False
            omap[h] = True
            process = True
            filename = 'data/athletes_outdoor.csv'
        elif h in imap and imap[h] == False:
            imap[h] = True
            process = True
            filename = 'data/athletes_indoor.csv'
        
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
                        cells.append(util.clean_text(ths[i]))
                else:
                    # use regular td tags
                    for i in range(len(tds)):
                        cells.append(util.clean_text(tds[i]))
                # skip table headers
                if len(cells) > 1:
                    cells = format_row(cells, event, indoor, athlete)
                    rows.append(cells)
    
    # save the table rows to the csv file
    if rows != [] and filename != '':
        mutex.acquire()
        print(f'[x] processed {len(rows)} entries')
        util.save_as_csv(rows, filename)   
        mutex.release()

# get all event data about an athlete if their data hasn't been gotten yet
def get_athlete_data(entries, athletes, ct):

    for athlete in entries:

        # if we have not processed this athlete ID yet
        mutex.acquire()
        if athlete[6] not in athletes:
            athletes[ct] = athlete[6]
            mutex.release()
            ct += 1        
        
            # get the soup
            soup = util.get_soup(athlete[2] if 'https:' in athlete[2] else 'https:' + athlete[2])

            # extract all the tables from the web page
            tables = soup.find_all('table')

            imap = {i: False for i in indoor_events}
            omap = {o: False for o in outoor_events}

            # iterate over all tables
            for i, table in enumerate(tables, start=1):
                # get all the rows of the table
                save_table_rows(table, athlete, imap, omap)
        else:
            mutex.release()
    return 0

# process the indoor or outdoor master file
def process_file(filename, athletes):
    with open(filename) as file:
        lines = list(csv.reader(file))
        t_len = len(lines) // NUM_CPUS

        ts = [None] * NUM_CPUS
        ct = len(athletes)
        athletes += [''] * len(lines)

        # each thread processes an equal amount of athletes excpet the last one which does the rest
        for i in range(NUM_CPUS):
            if i == NUM_CPUS - 1:
                ts[i] = Thread(target=get_athlete_data, args=[lines[t_len * i:], athletes, ct])
            else:
                ts[i] = Thread(target=get_athlete_data, args=[lines[t_len * i:t_len* (i + 1)], athletes, ct])
                ct += t_len
            ts[i].start()
        
        # join all threads
        for i in range(NUM_CPUS):
            ts[i].join()

# remove athlete files if they exist
if os.path.exists('data/athletes_outdoor.csv'):
    os.remove('data/athletes_outdoor.csv')
if os.path.exists('data/athletes_indoor.csv'):
    os.remove('data/athletes_indoor.csv')

# keep track of what ahtletes we have processed
athletes = []

# Process the master files
process_file(data/'master_indoor.csv', athletes)
process_file('data/master_outdoor.csv', athletes)

util.save_school_ids()
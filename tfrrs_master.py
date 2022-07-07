import tfrrs_util as util
import os

indoor_lists = [3492, 3157, 2770, 2324, 2124, 1797, 1569, 1345, 1139, 942, 769, 607, 502]
outdoor_lists = [3711, 3191, 2909, 2279, 1912, 1688, 1439, 1228, 1029, 840, 673]
indoor_events = ["60 Meters", "200 Meters", "400 Meters", "800 Meters", "Mile", "3000 Meters", "5000 Meters", "60 Hurdles"]
outoor_events = ["100 Meters", "200 Meters", "400 Meters", "800 Meters", "1500 Meters", "5000 Meters", "110 Hurdles", "400 Hurdles", "3000 Steeplechase"]
indoor_headers = ["PLACE", "ATHLETE", "URL", "TEAM", "MEET", "DATE", "ATHLETE_ID", "SCHOOL_ID", "YEAR", "EVENT", "TIME"]
outdoor_headers = ["PLACE", "ATHLETE", "URL", "TEAM", "MEET", "DATE", "ATHLETE_ID", "SCHOOL_ID", "YEAR", "WIND", "EVENT", "TIME"]

# given a table, returns all its rows
def get_table_rows(table, event, indoor):

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

# formats the given row into our desired format
def format_row(row, event, indoor):

    row[3] = util.format_grade(row[3])
    row[5] = util.format_time(row[5])
    row[7] = util.format_date(row[7])

    # returna and rearrange columns as: rank, name, url, school, meet, date, name id, school id, grade, [wind (or 0),] event, time
    return [row[0], row[1], row[2], row[4], row[6], row[7], util.get_athlete_id(row[2]), util.get_school_id(row[4]), row[3], event, row[5]] if indoor else [row[0], row[1], row[2], row[4], row[6], row[7], util.get_athlete_id(row[2]), util.get_school_id(row[4]), row[3], row[8] if len(row) == 9 else '0.0', event, row[5]]

# extract all the relevant tables from the given url
def processURL(url, event_list, indoor, filename):
    # get the soup
    soup = util.get_soup(url)
    # extract all the tables from the web page
    tables = soup.find_all("table")
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
        util.save_as_csv(rows, filename)
        count += 1


# get data for either the indoor or outdoor season
def get_data(indoor):

    # get what season we are doing and clear the file if it exists
    szn = "indoor" if indoor else "outdoor"
    szn_list = indoor_lists if indoor else outdoor_lists
    szn_events = indoor_events if indoor else outoor_events
    filename = f"master_{szn}.csv"
    if os.path.exists(filename):
        os.remove(filename)

    for lst in szn_list:
        processURL(f"https://www.tfrrs.org/lists/{lst}/2022_NCAA_Division_I_Outdoor_Qualifying_FINAL?limit=500", szn_events, indoor, filename)

    return 0

# Grab the master data
get_data(False)
get_data(True)

'''This is how you can get data from a single qualifying list'''
#processURL("https://www.tfrrs.org/lists/3492.html?limit=500&event_type=all&year=&gender=m", indoor_events, True, "indoor_2022.csv")
#processURL("https://www.tfrrs.org/lists/3711.html?limit=500&event_type=all&year=&gender=m", outoor_events, False, "outdoor_2022.csv")

#util.save_school_ids()
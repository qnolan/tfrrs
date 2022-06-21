import tfrrs_master as master

filenames = []

def process_file(filename):
    with open(filename) as file:
        for line in file:
            get_athlete_data(line[line.index('"') + 1: line.rindex('"')], line[line.rindex('"') + 2:].split(',')[1])


def convert_to_url(name, school):
    return "https://www.tfrrs.org/athletes/7722962/Oregon/Micah_Williams"

def get_athlete_data(name, school):
    if name not in filenames:
        filenames.append(name)

    if len(filenames) == 2:
        print(name)
        
        url = convert_to_url(name, school)

        # get the soup
        soup = master.get_soup(url)
        # extract all the tables from the web page
        tables = master.get_all_tables(soup)
        print(f"[+] Found a total of {len(tables)} tables.")

         # iterate over all tables
        count = 0
        for i, table in enumerate(tables, start=1):

            # get all the rows of the table
            rows = master.get_table_rows(table, "None")
            # save table as csv file
            table_name = f"table-{count}"
            print(f"[+] Saving {table_name}")
            master.save_as_csv(rows, "micah.csv")
            count += 1


    return 0

process_file("indoor_2022.csv")

print(f'[+] Found {len(filenames)} athletes')


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
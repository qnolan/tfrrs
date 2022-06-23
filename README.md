# tfrrs
The purpose of this project is to pull data from all top 500 D1 track and field athletes (per event) every year for the past 10 years.
I only considered some of the events in indoor and outdoor seasons (see the code for more detail on which ones).

This works by first getting all of the top 500 athletes per event per year and creates a master_{indoor,outdoor}.csv file with the data.
We then get the event history of each athlete in the master files and add this to athletes_{indoor,outdoor}.csv which will store all info about each athletes event history.

`tfrrs_athletes.py` has been optimized to use multithreading to get its task done using the number of CPUs found on the users computer. 
This could easily be done for the master files as well but those did not take too long for me to run.

## How to Run

I ran my code on `python3.8.10` and it works fine on that (I had problems on `python3.6.8` which I think was due to `BeautifulSoup`).

To get the master file data only run as:
```
python3 tfrrs_master.py
```
To get the master file data and athlete file data run as:
```
python3 tfrrs_athletes.py
```
To get the athlete file data only run as follows (make sure the below is commented out):
```
python3 tfrrs_athletes.py
```
To get the master data files uncomment the lines below (re-comment them once you have the master files):
```
'''Uncomment the two lines below to grab the master data'''
#get_data(False)
#get_data(True)
```

these lines are commented out so that you do not have to get the master data evertime that you run `tfrrs_athletes.py`

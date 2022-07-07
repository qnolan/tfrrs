from threading import Thread
import multiprocessing

NUM_CPUS = multiprocessing.cpu_count()

print('Number of CPUs: ', NUM_CPUS)

yo = range(353739)

total = sum(yo)

total_t = 0

def task(tasks, i, totals):
    sum = 0
    for t in tasks:
        sum += t
    totals[i] = sum
    return 0     
    
yo_len = len(yo)
t_len = yo_len // NUM_CPUS
brr = 0

print('yo_len:', yo_len, '\nt_len:', t_len)

ttl_t = [0] * NUM_CPUS
ts = [None] * NUM_CPUS


for i in range(NUM_CPUS): 
    if i == NUM_CPUS - 1:
        brr += len(yo)
        ts[i] = Thread(target=task, args=[yo, i, ttl_t])
        yo = []
    else: 
        brr += len(yo[:t_len])
        ts[i] = Thread(target=task, args=[yo[:t_len], i , ttl_t])
        yo = yo[t_len:]
    ts[i].start()

for i in range(NUM_CPUS):
    ts[i].join()

print('total:', total, '\nttl_t:', sum(ttl_t))

print('brr:', brr)
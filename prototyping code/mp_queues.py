#DOES NOT WORK IN AWS LAMBDA!
#/dev/shm is missing in the environment, so Queues won't work, results in: "OSError: [Errno 38] Function not implemented"

import hashlib
import secrets
import string
import time
from multiprocessing import Process, Queue

def create_hash(queue):
    while True:
        raw_value = queue.get()
        if raw_value != None:
            print(raw_value)
            #This is not a good example of actual password hashing. 
            #This is just meant to create a trivial load to show multithreading.
            hashed_value = hashlib.pbkdf2_hmac('sha256', raw_value.encode(), "salty-salt".encode(), 500000)
            print(hashed_value)
        else:
            break

if __name__ == '__main__':
    num_items = 200
    num_workers = 16
    workers = {}
    queue = Queue()
    #Our example workload will be password hashing (CPU intensive)
    #First, we create a list of random strings to hash and fill the queue
    alphabet = string.ascii_letters + string.digits
    for i in range(num_items):
        password = ''.join(secrets.choice(alphabet) for i in range(24))
        queue.put(password)

    #Just to make sure queue is full before proceeding
    assert queue.qsize() == num_items, "Queue not full"


    #Add easy markers that will tell workers to stop immediately (and not wait for timeout)
    for i in range(num_workers):
        queue.put(None)

    #Begin timer
    time_s = time.perf_counter()

    #Spawn all the workers we want
    for i in range(num_workers):
        workers[i] = Process(target=create_hash, args=(queue,))
        workers[i].start()

    #Join all workers (make main thread wait until all spawned workers have finished)
    for i in range(num_workers):
        workers[i].join()

    #End timer
    time_e = time.perf_counter()
    print("Proc time: " + str(time_e - time_s))

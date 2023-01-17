import hashlib
import json
import os
import secrets
import string
import time
from multiprocessing import Process

import DDBHelperFunc as ddb

def create_hash(raw_value):
    #This is not a good example of actual password hashing. 
    #This is just meant to create a trivial load to show multithreading.
    #Also explicitly NOT MEMORY-INTENSIVE, so that Lambda memory isn't an issue (only CPU)
    hashed_value = hashlib.pbkdf2_hmac('sha256', raw_value.encode(), "salty-salt".encode(), 100000)

def lambda_handler(event, context):
    num_items   = 200
    num_workers = int(os.environ['NUM_WORKERS'])
    workers     = {}
    passwords   = []

    #Our example workload will be password hashing (CPU intensive)
    #First, we create a list of random strings to hash
    alphabet = string.ascii_letters + string.digits
    for i in range(num_items):
        password = ''.join(secrets.choice(alphabet) for i in range(24))
        passwords.append(password)

    #Begin timer
    time_s = time.perf_counter()

    #Spawn all the workers we want, distributing our passwords to each one
    ctr=0
    for password in passwords:
        if ctr < num_workers:
            workers[ctr] = Process(target=create_hash, args=(password,))
            workers[ctr].start()
        else:
            #Join all workers (make main thread wait until all spawned workers have finished)
            #   We've reached the limit of workers, so we wait for them to finish before resuming work.
            for i in range(num_workers):
                workers[i].join()
            
            #Now that all workers have finished, start work on the current password,
            #   spawning the first of another batch of workers
            ctr=0
            workers[ctr] = Process(target=create_hash, args=(password,))
            workers[ctr].start()
        ctr+=1


    for i in range(num_workers):
        workers[i].join()

    #End timer
    time_e = time.perf_counter()
    
    response = ddb.write(payload={
        'workers': os.environ['NUM_WORKERS'],
        'memory': os.environ['MEMORY'],
        'arch': os.environ['ARCH'],
        'runtime': os.environ['RUNTIME'],
        'cores': os.cpu_count(),
        'proc_time': time_e - time_s
    })

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
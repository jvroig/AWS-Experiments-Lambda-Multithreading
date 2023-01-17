#Process the data set from the experiment

import csv
import json
import os
import boto3

#Get settings from SSM Parameter Store
ssm = boto3.client('ssm')
table = ssm.get_parameter(Name="LambdaMTExp_DDB_Table")['Parameter']['Value']
settings = json.loads(ssm.get_parameter(Name='LambdaMTExp_Settings')['Parameter']['Value'])

#Get experiment bucket name, so we can reference the code for the functions
Results_Bucket = os.environ['S3Bucket']
Results_Folder = "Results/"

s3  = boto3.client('s3')
ddb = boto3.client('dynamodb')

def map_results(record):
    pk = record.get('pk', {}).get('S', '')
    info = pk.split("_", 3)

    memory  = info[1]
    workers = info[2]
    arch    = info[3]

    data = {
        'Architecture': arch,
        'Memory': memory,
        'Workers': workers,
        'sk': record.get('sk', {}).get('S', ''),
        'cores': record.get('cores', {}).get('N', ''),
        'proc_time': record.get('proc_time', {}).get('N', ''),
    }
    return data

def get_results(pk):
    response = ddb.query(
        TableName=table,
        KeyConditionExpression='pk = :pk',
        ExpressionAttributeValues={
            ':pk': {'S': pk}
        }
    )
    raw = response.get('Items')
    items = []
    for record in raw:
        items.append(map_results(record))

    return items

def aggregate_results(items): 

    #Aggregate
    avg_time = 0.0
    total_proc_time = 0.0
    for item in items:
        arch = item['Architecture']
        memory = item['Memory']
        workers = item['Workers']
        cores = item['cores']
        total_proc_time += float(item['proc_time'])

    print("Aggregation Start")
    print(total_proc_time)
    print(len(items))
    avg_time = total_proc_time / len(items)
    print(avg_time)
    print("Aggregation End")

    data = {
        'Architecture': arch,
        'Memory': memory,
        'Workers': workers,
        'cores': cores,
        'avg_proc_time': avg_time,
    }
    return data

    

def lambda_handler(event, context):
    runtimes = settings['Runtimes']
    archs    = settings['Architectures']
    memsizes = settings['MemorySizes']
    workers  = settings['Workers']

    ctr=0
    collected_items = []
    for runtime in runtimes:
        for arch in archs:
            for mem in memsizes:
                for num_workers in workers:
                    pk = "Lambda_" + mem + "_" + str(num_workers) + "_" + arch

                    print("Getting results for: " + pk + "...")
                    items = get_results(pk)
                    
                    #Write individual results to S3 as CSV file
                    # filename = pk + ".csv"
                    # csv_file = open("/tmp/" + filename, 'w', newline='')
                    # csv_writer = csv.DictWriter(csv_file, fieldnames=items[0].keys())
                    # csv_writer.writeheader()
                    # for item in items:
                    #     csv_writer.writerow(item)
                    # csv_file.close()

                    # s3.upload_file('/tmp/' + filename, Results_Bucket, Results_Folder + filename)

                    #Aggregate results
                    aggregated = aggregate_results(items)
                    collected_items.append(aggregated)


    filename = "AggregatedResults.csv"
    csv_file = open("/tmp/" + filename, 'w', newline='')
    csv_writer = csv.DictWriter(csv_file, fieldnames=['Architecture','Memory','Workers','cores','avg_proc_time'])
    csv_writer.writeheader()
    for item in collected_items:
        csv_writer.writerow(item)
    csv_file.close()

    s3.upload_file('/tmp/' + filename, Results_Bucket, Results_Folder + filename)

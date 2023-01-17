#Experiment invoker: will be triggered by CloudWatch Events, and then will trigger all the Lambda functions in sequence

import os
import json
import time

import boto3

lambda_client = boto3.client('lambda')
ssm = boto3.client('ssm')
settings = json.loads(ssm.get_parameter(Name='LambdaMTExp_Settings')['Parameter']['Value'])

def lambda_handler(event, context):
    
    runtimes = settings['Runtimes']
    archs    = settings['Architectures']
    memsizes = settings['MemorySizes']
    workers  = settings['Workers']

    for runtime in runtimes:
        for arch in archs:
            for mem in memsizes:
                for num_workers in workers:
                    function_name = "LambdaMTExp_" + mem + "_" + str(num_workers) + "_" + arch

                    response = lambda_client.invoke(FunctionName=function_name, InvocationType='Event')
                    print("OK: " + function_name)

    return {
        'statusCode': 200,
        'body': json.dumps("Lambdapocalypse: Lambda MT experiment")
    }
#Will create all the different lambdas to be invoked by the experiment.

import os
import json
from multiprocessing import Process
import time
import boto3
from crhelper import CfnResource

#Get settings from SSM Parameter Store
ssm = boto3.client('ssm')
lmb = boto3.client('lambda')
settings = json.loads(ssm.get_parameter(Name='LambdaMTExp_Settings')['Parameter']['Value'])

#Get LambdaMTExp_Layer ARN, so we can attach to the functions to be created.
LambdaMTExp_Layer_ARN = os.environ['LambdaMTExp_Layer_ARN']

#Get experiment bucket name, so we can reference the code for the functions
Code_Bucket = os.environ['S3Bucket']

#Lambda execution roles for all created Lambda functions
LambdaServiceRole = os.environ['LambdaServiceRole']

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

def worker_task(data):
    runtime = data['runtime'] 
    arch = data['arch']
    mem = data['mem']
    num_workers = data['num_workers']
    function_name = "LambdaMTExp_" + mem + "_" + str(num_workers) + "_" + arch

    response = lmb.create_function(
        FunctionName=function_name,
        Runtime=runtime,
        MemorySize=int(mem),
        Architectures=[arch],
        Timeout=900,
        Layers=[LambdaMTExp_Layer_ARN],
        Code={
            'S3Bucket': Code_Bucket,
            'S3Key': "Lambdas/mp_noQueue.zip",
        },
        Handler="mp_noQueue.lambda_handler",
        Environment={
            'Variables': {
                "RUNTIME": runtime,
                "MEMORY": mem,
                "ARCH": arch,
                "NUM_WORKERS": str(num_workers)
            }
        },
        Role=LambdaServiceRole
    )

@helper.create
@helper.update
def create_lambdas(event, _):
    runtimes = settings['Runtimes']
    archs    = settings['Architectures']
    memsizes = settings['MemorySizes']
    workers  = settings['Workers']

    process_workers = {} 
    max_threads = 4

    ctr=0
    for runtime in runtimes:
        for arch in archs:
            for mem in memsizes:
                for num_workers in workers:
                    if ctr >= max_threads:
                        for i in range(max_threads):
                            process_workers[i].join()
                        ctr = 0

                    data = {
                        'runtime': runtime,
                        'arch': arch,
                        'mem': mem,
                        'num_workers': num_workers,
                    }

                    process_workers[ctr] = Process(target=worker_task, args=(data,))
                    process_workers[ctr].start()
                    ctr += 1


    for i in range(max_threads):
        process_workers[i].join()


def lambda_handler(event, context):
    helper(event, context)

@helper.delete
def delete_action(event, _):
    print("Delete action - no action...(should be deleting created Lambdas, but not yet supported")
    #For future implem:
    # Use boto3, search for all lambdas using naming convention, delete each one

'''
        Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
        SPDX-License-Identifier: MIT-0
'''

import json
import boto3
import time
import os
import re
import myq
from boto3 import resource
from boto3.dynamodb.conditions import Key

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
iotClient = boto3.client('iot-data')

# The boto3 dynamoDB resource
dynamodb_resource = resource('dynamodb')


def lambda_handler(event, context):

    utime = str(int(time.time())) #Current Unix Time
    plate_detected = False
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    image = {
        'S3Object': {
            'Bucket': bucket,
            'Name': key,
            }
        }
    response = rekognition.detect_labels(Image=image, MaxLabels=20, MinConfidence=50)
    for object in response["Labels"]:
        if object["Name"] == "License Plate":
            plate_detected = True
            break
    if plate_detected:
        PlateNumber = rekognition.detect_text(Image=image)
        PlateNumber = PlateNumber['TextDetections'][1]['DetectedText']
        PlateNumber = re.sub('[^a-zA-Z0-9 \n\.]', '', PlateNumber).replace(" ","")
        print (PlateNumber)

        match = match_plate("CarInfo", "LicensePlate", PlateNumber)

        if match == 1:
            print ('License Plate Match Found')
            # This is the name of the garage door as listed in the MYQ application, change to whatever suits your needs.
            x = myq.myqapi()
            x.set_state("Garage Door")
        else:
            print ('License Plate Match Not Found')

    else:
        print ('License Plate not found in the image')

def match_plate(table_name, filter_key, filter_value):
    """
    Perform a query operation on the table.
    Can specify filter_key (col name) and its value to be filtered.
    """
    table = dynamodb_resource.Table(table_name)
    filtering_exp = Key(filter_key).eq(filter_value)
    response = table.query(KeyConditionExpression=filtering_exp)

    return response['Count']
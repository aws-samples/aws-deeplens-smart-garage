'''
        Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
        SPDX-License-Identifier: MIT-0

        Disclaimer: The code here can vary depends on the atual hardware maker and 
        The authors claim no responsibility for damages to your garage door or property by use of the code within.
'''

import requests
import boto3
import time
import os
import json

class myqapi:
	# These constants can vary depends on the atual hardware maker
        app_id = os.environ['APP_ID']
        device_list_endpoint = os.environ['DEVICE_LIST_ENDPOINT']
        device_set_endpoint = os.environ['DEVICE_SET_ENDPOINT']
        uri = os.environ['BASE_URI']
        endpoint = os.environ['BASE_ENDPOINT']

    #retrive MyQ username and password from aws secret manager
        secret_name = os.environ['SECRET_NAME']
        # Create a Secrets Manager client
        session = boto3.session.Session()
        region_name = session.region_name
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
            print(get_secret_value_response)
        except ClientError as e:
            print(e)
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
                j = json.loads(secret)
                password = j['myq_password']
                username = j['myq_username']
            else:
                decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
                username = decoded_binary_secret.myq_username
                password = decoded_binary_secret.myq_password

        def __init__(self):
		# Get the security token used to authenticate to myq API
                params = {
                    'username': self.username,
                    'password': self.password
                }
                login = requests.post(
                        'https://{host_uri}/{login_endpoint}'.format(
                            host_uri=self.uri,
                            login_endpoint=self.endpoint),
                            json=params,
                            headers={
                                'MyQApplicationId': self.app_id
                            }
                    )

                auth = login.json()
                self.security_token = auth['SecurityToken']
                print (auth['SecurityToken'])

        def get_devices(self):
		# Gets all devices within your myQ account
                devices = requests.get(
                    'https://{host_uri}/{device_list_endpoint}'.format(
                        host_uri=self.uri,
                        device_list_endpoint=self.device_list_endpoint),
                        headers={
                            'MyQApplicationId': self.app_id,
                            'SecurityToken': self.security_token
                        }
                )

                devices = devices.json()['Devices']
                return devices

        def get_garagedeviceid(self, description):
		# This gets the device id for the garage door state will be set on
                devices = self.get_devices()
                deviceid = None
                garagedoors = [x for x in devices if x['MyQDeviceTypeName'] == 'Garage Door Opener WGDO']

                for garagedoor in garagedoors:
                        for attrib in garagedoor['Attributes']:
                                if attrib['Value'] == description:
                                        deviceid = garagedoor['MyQDeviceId']
                if deviceid == None:
                        return "Liftmaster device name not found"
                else:
                        return deviceid

        def get_state(self, description):
		# This gets the state of a garage door
                deviceid = self.get_garagedeviceid(description)
                devices = self.get_devices()
                garagedoors = [x for x in devices if x['MyQDeviceTypeName'] == 'Garage Door Opener WGDO']
                print (garagedoors)
                garagedoor = garagedoors[0]['Attributes']
                state = [x['Value'] for x in garagedoor if x['AttributeDisplayName'] == "doorstate"]

                return state[0]

        def set_state(self, description):
		# state = 2 (close) and state = 1 (open)
                state = self.get_state(description)
                device_id = self.get_garagedeviceid(description)
                if state == "2":
                    new_state = "1"

                payload = {
                    'attributeName': 'desireddoorstate',
                    'myQDeviceId': device_id,
                    'AttributeValue': new_state,
                }
                device_action = requests.put(
                    'https://{host_uri}/{device_set_endpoint}'.format(
                        host_uri=self.uri,
                        device_set_endpoint=self.device_set_endpoint),
                        data=payload,
                        headers={
                            'MyQApplicationId': self.app_id,
                            'SecurityToken': self.security_token
                        }
                )

                # wait 60 sec and close the gate
                time.sleep(60)
                new_state = "2"

                payload = {
                    'attributeName': 'desireddoorstate',
                    'myQDeviceId': device_id,
                    'AttributeValue': new_state,
                }
                device_action = requests.put(
                    'https://{host_uri}/{device_set_endpoint}'.format(
                        host_uri=self.uri,
                        device_set_endpoint=self.device_set_endpoint),
                        data=payload,
                        headers={
                            'MyQApplicationId': self.app_id,
                            'SecurityToken': self.security_token
                        }
                )

                return device_action.status_code == 200

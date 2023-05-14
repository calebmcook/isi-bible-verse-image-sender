import os
import json
from twilio.rest import Client
import boto3
from boto3.dynamodb.conditions import Attr, Key
import logging
from datetime import date
import random
#from awswrangler import s3

logger = logging.getLogger(__name__)

##LAMBDA CODE###
def handler(event, context):
    #query all the object locations from dynamodb table
    dynamodb = boto3.resource('dynamodb')
    clients_table = dynamodb.Table('isi-bible-verse-clients-db3-dev')

    #scan for only subscribers to hope in numbers and pull out their phone numbers
    subscribers = clients_table.scan(FilterExpression=Attr('current_status').eq('DAILY-IMAGE')|Attr('current_status').eq('ALL'))
    
    subscriber_numbers = [k['phone_number'] for k in subscribers['Items']]

    #access twilio credentials through environment variables
    #get twilio auth token from AWS systems manager parameter store
    ssm = boto3.client('ssm')
    account_sid = ssm.get_parameter(
        Name='/twilio/garretson_technology_isi_subaccount/twilio_account_sid',
        WithDecryption=True
    )['Parameter']['Value']

    auth_token = ssm.get_parameter(
        Name='/twilio/garretson_technology_isi_subaccount/twilio_auth_token',
        WithDecryption=True
    )['Parameter']['Value']
    
    #list all verse image objects and choose random object
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('isi-bible-verse-images')
    my_key = random.choice(list(bucket.objects.all())).key
    image_url = f'https://{bucket.name}.s3.amazonaws.com/{my_key}'

    #create twilio client and create message
    client = Client(account_sid, auth_token)
    
    for phone_num in subscriber_numbers:
        try: 
            message = client.messages.create(
                        body='"STOP-SERVICES" to unsubscribe.',
                        #from_='+19287678011',
                        from_='+16022231114',
                        send_as_mms=True,
                        media_url=image_url,
                        to=phone_num
                )
            logger.warning(message)

        except Exception as err:
            logger.warning("Couldn't send message to number %s.",
                    phone_num)
            continue

    return {
        'statusCode': 200,
    }
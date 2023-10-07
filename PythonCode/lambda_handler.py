import json
import boto3
import traceback

def lambda_handler(event, context):
    # look for a valid JSON, in this case an id exists
    if 'id' in event:
        hasError = False
        # list to keep track of any errors that might have occured
        errorsPayload = []
        try:
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('tripped_sla_items')
            # loop through each folder
            for sla_errors in event['sla_error']:
                # loop through each file
                for files in sla_errors['files']:
                    # attemp to store in dynamodb
                    response = table.put_item(
                        Item={
                            'sla_date': event['createdAt'],
                            # date format is yyyy-MM-dd instead of yyyy-MM-dd HH:mm:ss
                            'file_created_date': files['creationDate'].split()[0],
                            'folder_name': sla_errors['folder'],
                            'sla_minutes': sla_errors['sla'],
                            'file_name': files['filename']
                        }
                    )
                    # NOTE: we're assuming here that we want to process all records and record any errors along the way instead of quitting out after 1 fail
                    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                        errorsPayload.append(response)
        except:
            errorsPayload.append(traceback.format_exc())
    else:
        # return 400 for user error, in this case malformed JSON (can be any arbitrary rule)
        return lambda_response_code('Malformed JSON input.', 400)
    
    # return 200 if success
    if(len(errorsPayload) == 0):
        return lambda_response_code('Success.', 200)
    else:
        # return 500 for internal system issues
        return lambda_response_code(errorsPayload, 500)

def lambda_response_code(payload, responseCode):
    message = dict(statusCode=responseCode,
                   isBase64Encoded=False,
                   headers={'Content-Type': 'application/json'},
                   body=payload)
    return json.dumps(message)
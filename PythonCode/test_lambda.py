from attr import dataclass
import pytest
from lambda_handler import lambda_handler
import json
import boto3
from moto import mock_dynamodb2

from contextlib import contextmanager

# reference https://towardsdatascience.com/moto-pytest-and-aws-databases-a-quality-and-data-engineering-crossroads-ae58f9e7b265

@contextmanager
def create_table(dynamodb_client):
    """Create mock DynamoDB table to test full CRUD operations"""

    dynamodb_client.create_table(
        TableName="tripped_sla_items",
        KeySchema=[
            # partition key by API response date
            {
                'AttributeName': 'sla_date',
                'KeyType': 'HASH'
            },
            # sort keys
            {
                'AttributeName': 'file_created_date',
                'KeyType': 'RANGE'
            },
            {
                'AttributeName': 'folder_name',
                'KeyType': 'RANGE'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'sla_date',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'file_created_date',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'folder_name',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            # start with 10 reads/writes per second vs on demand
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    yield

@pytest.fixture
def context():
    @dataclass
    class LambdaContext:
        function_name: str = "sla_items_lambda"
        aws_request_id: str = "88888888-4444-4444-4444-121212121212"
        invoked_function_arn: str = "arn:aws:lambda:us-east-1:123456789101:function:sla_items_lambda"
    return LambdaContext()

@mock_dynamodb2
def test_lambda_success(context):
    # had an issue where file was saved as UTF-16 and it wasn't loading
    with open("C:\\Experian\\PythonCode\\request.json") as json_file:
        json_data = json.load(json_file)
        client = boto3.resource('dynamodb', region_name='us-east-1')
        with create_table(client):
            response = json.loads(lambda_handler(json_data, context))
            assert response['statusCode'] == 200

@mock_dynamodb2
def test_lambda_malformed_request(context):
    # had an issue where file was saved as UTF-16 and it wasn't loading
    with open("C:\\Experian\\PythonCode\\malformed_request.json") as json_file:
        json_data = json.load(json_file)
        client = boto3.resource('dynamodb', region_name='us-east-1')
        with create_table(client):
            response = json.loads(lambda_handler(json_data, context))
            print(response)
            assert response['statusCode'] == 400

@mock_dynamodb2
def test_lambda_errored_request(context):
    # had an issue where file was saved as UTF-16 and it wasn't loading
    with open("C:\\Experian\\PythonCode\\error_request.json") as json_file:
        json_data = json.load(json_file)
        client = boto3.resource('dynamodb', region_name='us-east-1')
        with create_table(client):
            response = json.loads(lambda_handler(json_data, context))
            assert response['statusCode'] == 500
            print(response['body'])
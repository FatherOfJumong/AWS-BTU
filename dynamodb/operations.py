import boto3
from botocore.exceptions import ClientError

def list_dynamodb_tables(dynamodb_client):
    try:
        response = dynamodb_client.list_tables()
        table_names = response['TableNames']
        
        if not table_names:
            print("No DynamoDB tables found.")
            return []
        
        print("DynamoDB Tables:")
        for table_name in table_names:
            print(f"  {table_name}")
        
        return table_names
    except ClientError as e:
        print(f"Error listing DynamoDB tables: {e}")
        return []
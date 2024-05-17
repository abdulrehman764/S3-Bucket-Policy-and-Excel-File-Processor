import json
import boto3
import pandas as pd
import io
from datetime import datetime
def get_aws_account_arns_from_key_metadata(key_metadata):
    """
    Extracts unique AWS account ARNs from the KMS key metadata excluding the root account.

    Args:
        key_metadata (dict): Metadata for the KMS key.

    Returns:
        list: List of unique AWS account ARNs excluding the root account.
    """
    account_arns = set()  # Using a set to ensure uniqueness
    key_policy = json.loads(key_metadata['Policy'])
    for statement in key_policy['Statement']:
        if 'Principal' in statement:
            principal = statement['Principal']
            if 'AWS' in principal:
                if isinstance(principal['AWS'], str):
                    # Check if the principal is not the root account
                    if not principal['AWS'].endswith(':root'):
                        account_arns.add(principal['AWS'])
                elif isinstance(principal['AWS'], list):
                    for arn in principal['AWS']:
                        # Check if the principal is not the root account
                        if not arn.endswith(':root'):
                            account_arns.add(arn)
    return list(account_arns)

def attach_bucket_policy(bucket_name, account_arns):
    """
    Attaches a bucket policy to the S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        account_arns (list): List of ARNs of AWS accounts.

    Returns:
        None
    """
    s3_client = boto3.client('s3')
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "NotPrincipal": {
                    "AWS": account_arns
                },
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            }
        ]
    }
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": account_arns
                },
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            },
            {
                "Effect": "Deny",
                 "NotPrincipal": {
                    "AWS": account_arns
                },
                "Action": "s3:GetObject",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            }
        ]
    }
    bucket_policy_str = json.dumps(bucket_policy)
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_str)

def get_kms_key_metadata(key_arn):
    """
    Retrieves metadata for a KMS key using its ARN.

    Args:
        key_arn (str): The ARN of the KMS key.

    Returns:
        dict: Metadata for the KMS key.
    """
    kms_client = boto3.client('kms')
    return kms_client.get_key_policy(KeyId=key_arn, PolicyName='default')


def get_kms_master_key(bucket_name):
    """
    Retrieves the KMS master key ID associated with server-side encryption for the given S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.

    Returns:
        str: The KMS master key ID if found, otherwise None.
    """
    # Initialize the S3 client
    s3_client = boto3.client('s3')

    # Get encryption settings for the bucket
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)

    # Check if encryption is enabled for the bucket
    if 'ServerSideEncryptionConfiguration' in response:
        encryption_config = response['ServerSideEncryptionConfiguration']
        for rule in encryption_config['Rules']:
            if 'ApplyServerSideEncryptionByDefault' in rule:
                sse_algorithm = rule['ApplyServerSideEncryptionByDefault'].get('SSEAlgorithm')
                if sse_algorithm == 'aws:kms':
                    return rule['ApplyServerSideEncryptionByDefault'].get('KMSMasterKeyID')
    return None
    
def lambda_handler(event, context):
    # Get the S3 bucket and key where the file was uploaded
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = event['Records'][0]['s3']['object']['key']
    
    print(f"Bucket: {source_bucket} , Key: {source_key}")
    
    # Get the filename and extension
    file_name = source_key.split('/')[-1]
    file_prefix = file_name.split('.')[0]
    file_extension = file_name.split('.')[-1]
    
    print(f"File: {file_name} , Prefix: {file_prefix}, Extension: {file_extension}")
    
    # Check if the uploaded file is an Excel file
    if file_extension.lower() == 'xlsx':
        # Extract date information from the filename
        date_str = file_name.split('_')[1]
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day

        # Download the file from S3
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        excel_data = response['Body'].read()

        # Convert Excel data to DataFrame
        excel_df = pd.read_excel(io.BytesIO(excel_data), header=None)
        excel_df = excel_df.dropna(how='all').dropna(axis=1, how='all')
        headers = excel_df.iloc[0]
        excel_df = pd.DataFrame(excel_df.values[1:], columns=headers)

        # Convert DataFrame to CSV
        csv_data = excel_df.to_csv(index=False)

        # Upload the CSV to another S3 bucket encrypted with KMS
        target_bucket = 'input-data-bucket-eu-west-2'
        target_key = f"year={year}/month={month:02d}/day={day:02d}/{file_prefix}.csv"
        s3_client.put_object(
            Bucket=target_bucket,
            Key=target_key,
            Body=csv_data
            # ServerSideEncryption='aws:kms',
            # SSEKMSKeyId=kms_key_arn
        )
        
        
        key_arn = get_kms_master_key(target_bucket)
        key_metadata = get_kms_key_metadata(key_arn)
        aws_account_arns = get_aws_account_arns_from_key_metadata(key_metadata)
        print("AWS Account ARNs:", aws_account_arns)
        attach_bucket_policy(target_bucket, aws_account_arns)
        print("Policy attached for all accounts.")


        # Run Glue crawler
        glue_client = boto3.client('glue')
        glue_client.start_crawler(Name='s3_input_crawler')

        return {
            'statusCode': 200,
            'body': f'File {file_name} converted and stored as {target_key} in {target_bucket}'
        }
    else:
        return {
            'statusCode': 400,
            'body': f'Error: {file_name} is not an Excel file'
        }

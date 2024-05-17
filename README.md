# S3 Bucket Policy and Excel File Processor

This repository contains a set of Python functions and an AWS Lambda handler to process uploaded Excel files in an S3 bucket, convert them to CSV format, and attach bucket policies based on the metadata of KMS keys. The Lambda function is designed to trigger upon file uploads to an S3 bucket, convert Excel files to CSV, and handle associated S3 and KMS configurations.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Functions](#functions)
  - [get_aws_account_arns_from_key_metadata](#get_aws_account_arns_from_key_metadata)
  - [attach_bucket_policy](#attach_bucket_policy)
  - [get_kms_key_metadata](#get_kms_key_metadata)
  - [get_kms_master_key](#get_kms_master_key)
  - [lambda_handler](#lambda_handler)
- [License](#license)

## Installation

To set up the environment for this project, follow these steps:

1. **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/repo-name.git
    cd repo-name
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up AWS credentials:**
    Ensure your AWS credentials are configured. You can do this by setting up the `~/.aws/credentials` file or using environment variables:
    ```sh
    export AWS_ACCESS_KEY_ID=your_access_key_id
    export AWS_SECRET_ACCESS_KEY=your_secret_access_key
    export AWS_DEFAULT_REGION=your_default_region
    ```

## Usage

This project is primarily designed to be deployed as an AWS Lambda function triggered by S3 events. Below are the steps to deploy and test the function locally:

1. **Deploy the Lambda function:**
    - Package the code and dependencies.
    - Create a Lambda function via the AWS Management Console or using the AWS CLI.
    - Set up the S3 trigger for the Lambda function.

2. **Test locally:**
    You can simulate the Lambda function locally by creating an event JSON file similar to the structure of S3 event notifications and running the handler.

## Functions

### `get_aws_account_arns_from_key_metadata`

Extracts unique AWS account ARNs from the KMS key metadata excluding the root account.

#### Args:
- `key_metadata` (dict): Metadata for the KMS key.

#### Returns:
- `list`: List of unique AWS account ARNs excluding the root account.

### `attach_bucket_policy`

Attaches a bucket policy to the S3 bucket.

#### Args:
- `bucket_name` (str): The name of the S3 bucket.
- `account_arns` (list): List of ARNs of AWS accounts.

#### Returns:
- None

### `get_kms_key_metadata`

Retrieves metadata for a KMS key using its ARN.

#### Args:
- `key_arn` (str): The ARN of the KMS key.

#### Returns:
- `dict`: Metadata for the KMS key.

### `get_kms_master_key`

Retrieves the KMS master key ID associated with server-side encryption for the given S3 bucket.

#### Args:
- `bucket_name` (str): The name of the S3 bucket.

#### Returns:
- `str`: The KMS master key ID if found, otherwise `None`.

### `lambda_handler`

AWS Lambda handler function triggered by S3 events to process uploaded Excel files.

#### Args:
- `event` (dict): Event data passed by AWS Lambda.
- `context` (object): Runtime information provided by AWS Lambda.

#### Returns:
- `dict`: Status code and message body indicating the result of the operation.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

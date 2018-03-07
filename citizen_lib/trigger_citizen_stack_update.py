# Copyright 2017 Insurance Australia Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This python module is for triggering citizen stacks to be updated via SNS
"""
import os
import json
import sys
import boto3
from configuration.initialise_config import watchmen_vars

CANARY_ACCOUNTS = watchmen_vars.CanaryAccounts

if watchmen_vars.UseAWSOrganisations:
    AWS_MASTER_ACCOUNT_ROLE_ARN = watchmen_vars.MasterAccountRoleArn
else:
    AWS_MASTER_ACCOUNT_ROLE_ARN = ""

PREFIX = os.environ['prefix'] if "prefix" in os.environ else ""
SNS_ARN = os.environ['SNS_ARN'] if "SNS_ARN" in os.environ else ""
CITIZEN_S3_BUCKET = os.environ['CITIZEN_S3_BUCKET'] if "CITIZEN_S3_BUCKET" in os.environ else ""

def get_canary_accounts():
    """
    Get canary accounts
    """
    return set(CANARY_ACCOUNTS)

def get_other_aws_accounts():
    """
    Get all other accounts
    """
    return (get_csv_accounts() | get_organizations_accounts()) - get_canary_accounts()

def get_csv_accounts():
    """
    Get unique accounts from csv
    """
    with open("./accounts/aws_accounts.csv") as filer:
        lines = filer.readlines()
    return {line.split(",")[0] for line in lines}

def get_organizations_accounts():
    """
    Get unique accounts from organizations
    Was getting endpoint error so explicitly define region and end point
    according to http://docs.aws.amazon.com/general/latest/gr/rande.html?shortFooter=true
    """
    org_accounts = set()

    if AWS_MASTER_ACCOUNT_ROLE_ARN:
        sts = boto3.client(
            "sts",
            region_name='ap-southeast-2',
            endpoint_url='https://sts.ap-southeast-2.amazonaws.com',
            verify=False
        )

        paginator = boto3.client(
            "organizations",
            region_name='us-east-1',
            endpoint_url='https://organizations.us-east-1.amazonaws.com',
            verify=False,
            **get_assumed_creds(sts, AWS_MASTER_ACCOUNT_ROLE_ARN)
        ).get_paginator("list_accounts")

        for page in paginator.paginate():
            for account in page['Accounts']:
                org_accounts.add(str(account[u'Id']))

    return org_accounts


def get_assumed_creds(sts, arn):
    """
    Gets assume role credentials
    """
    if arn:
        credentials = sts.assume_role(RoleArn=arn, RoleSessionName="AssumeRoleSession1")
        return {
            "aws_access_key_id": credentials["Credentials"]['AccessKeyId'],
            "aws_secret_access_key": credentials["Credentials"]['SecretAccessKey'],
            "aws_session_token": credentials["Credentials"]['SessionToken']
        }
    else:
        return {}

def get_sns_message(aws_accounts):
    """
    Construct SNS message
    """
    aws_accounts = str(aws_accounts).replace("['", "").replace("']", "").replace("', '", " ")

    # Construct the SNS Message for aws_accounts
    data = {}
    data['prefix'] = PREFIX
    data['bucket'] = CITIZEN_S3_BUCKET
    data['accounts'] = aws_accounts

    return json.dumps(data)

def get_account_type():
    """
    Read module input and set account type
    """
    account_type = ""

    if len(sys.argv) >= 2:
        account_type = sys.argv[1]

    return account_type

def main():
    """
    Main method
    """
    account_type = get_account_type()

    if account_type == "CanaryAccounts":  # Trigger Update Citizen stack for CanaryAccounts defined in 'configuration/config.yml' file
        aws_accounts = list(get_canary_accounts())
    elif account_type == "ProductionAccounts": # Trigger Update Citizen stack for ProductionAccounts from 'AWS Org' and 'aws_accounts.csv' (excluding canary accounts)
        aws_accounts = list(get_other_aws_accounts())
    else:
        raise Exception("Account type '{}' not found".format(account_type))

    sns_message = get_sns_message(aws_accounts)
    print "SNS Message for {}: {}".format(account_type, sns_message)

    response = boto3.client('sns', verify=False).publish(TargetArn=SNS_ARN, Message=sns_message)
    print "Published to SNS Topic. Response: {}".format(response)

if __name__ == "__main__":
    main()

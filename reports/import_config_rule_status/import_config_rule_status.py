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
Imports all Citizen config rules statuses into a DynamoDB table.
"""
from datetime import datetime
import json
import re
import boto3

MAX_ITEMS = 25

def log_info(info):
    """Prints the specified information to output.

    Args:
        info: Information to print
    """
    print json.dumps(info)

def get_assumed_creds(sts, arn):
    """Retrieves the AWS assume role credentials.

    Args:
        sts: boto3 sts object
        arn: Arn of the role we want to assume

    Returns:
        AWS credentials
    """
    if arn:
        credentials = sts.assume_role(
            RoleArn=arn,
            RoleSessionName="AssumeRoleSession1"
        )["Credentials"]

        result = {
            "aws_access_key_id": credentials['AccessKeyId'],
            "aws_secret_access_key": credentials['SecretAccessKey'],
            "aws_session_token": credentials['SessionToken']
        }
    else:
        result = {}

    return result

def get_table_items(dynamodb, table_name):
    """Retrieves all rows from the specified DynamoDB table.

    Args:
        dynamodb: boto3 DynamoDB object
        table_name: Table we want to retrieve the records from

    Returns:
        List of items from the table
    """
    table_items = []

    for page in dynamodb.get_paginator("scan").paginate(TableName=table_name):
        table_items += page["Items"]

    return table_items

def get_config_rules_statuses(config):
    """Retrieves all of the AWS Config rules.

    Args:
        config: boto3 config object

    Returns:
        List of AWS Config rules
    """
    config_rules = []
    page_iterator = config.get_paginator("describe_compliance_by_config_rule")

    for page in page_iterator.paginate():
        config_rules += page["ComplianceByConfigRules"]

    return config_rules

def get_config_rules_sources(config):
    """Gets the config rules and their associated lambda arn.

    Args:
        config: boto3 config object

    Returns:
        Dictionary containing the config rules and their associated lambda arn
    """
    config_rules = {}
    page_iterator = config.get_paginator("describe_config_rules")

    for page in page_iterator.paginate():
        for rule in page["ConfigRules"]:
            # Get the source lambda arn of the config rule
            config_rules[rule["ConfigRuleName"]] = rule["Source"]["SourceIdentifier"]

    return config_rules

def get_config_rule_invoke_success(config, rule_name):
    """Compares the config rule's last successful invocation time
    and the last success evaluation time and
    returns success or failed if eval time is older than inovke time.

    Args:
        config: boto3 config object
        rule_name: config rule name

    Returns:
        Last successful invoke time
        Success or failed invocation
    """
    rule_status = config.describe_config_rule_evaluation_status(ConfigRuleNames=[rule_name])
    rule_invocation_time = rule_status['ConfigRulesEvaluationStatus'][0]['LastSuccessfulInvocationTime']
    rule_eval_time = rule_status['ConfigRulesEvaluationStatus'][0]['LastSuccessfulEvaluationTime']

    if  rule_invocation_time < rule_eval_time:
        invocation_result = "SUCCESS"
    else:
        invocation_result = "FAIL"

    return rule_invocation_time, invocation_result

def import_config_rule_statuses(table_name, citizen_account, sts, dynamodb, timestamp, prefix):
    """Adds records into a DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        citizen_account: Main field values to add in the table
        sts: boto3 sts object
        dynamodb: boto3 dynamodb object
        timestamp: Time stamp
    """
    try:
        assumed_creds = get_assumed_creds(sts, citizen_account["ExecutionRoleArn"]["S"])

    except Exception:
        log_info(
            "Failed to get config rule statuses for account {}".format(
                citizen_account["AccountId"]["S"]
            )
        )

        rule_item = {
            "AccountId": {"S": citizen_account["AccountId"]["S"]},
            "AccountName": {"S": citizen_account["AccountName"]["S"]},
            "RuleName": {"S": "Undefined"},
            "ImportRunTimestamp": {"S": timestamp}
        }

        response = dynamodb.put_item(TableName=table_name, Item=rule_item, ReturnConsumedCapacity="INDEXES")
        print(response)

        return

    items = []
    config = boto3.client("config", **assumed_creds)
    config_rules_sources = get_config_rules_sources(config)

    # For each config rule
    for rule_status in get_config_rules_statuses(config):
        rule_lambda_arn = config_rules_sources[rule_status["ConfigRuleName"]]

        # If the config rule's source lambda arn matches the proxy lambda arn,
        # then it is a Watchmen rule
        if re.match(
                r"arn:aws:lambda:ap-southeast-2:\d+:function:{}ProxyLambda".format(prefix),
                rule_lambda_arn
            ):
            rule_invocation_time, invocation_result = get_config_rule_invoke_success(config, rule_status["ConfigRuleName"])
            rule_item = {
                "AccountId": {"S": citizen_account["AccountId"]["S"]},
                "AccountName": {"S": citizen_account["AccountName"]["S"]},
                "RuleName": {"S": rule_status["ConfigRuleName"]},
                "ComplianceType": {"S": rule_status["Compliance"]["ComplianceType"]},
                "InvokeTime": {"S": rule_invocation_time.isoformat()},
                "InvokeStatus": {"S": invocation_result},
                "ImportRunTimestamp": {"S": timestamp}
            }

            items.append({"PutRequest": {"Item": rule_item}})

            if len(items) == MAX_ITEMS:
                response = dynamodb.batch_write_item(RequestItems={table_name: items}, ReturnConsumedCapacity="INDEXES")
                print(response)
                items = []

    # If there are some items still left
    if items:
        response = dynamodb.batch_write_item(RequestItems={table_name: items}, ReturnConsumedCapacity="INDEXES")
        print(response)

def delete_all_items(dynamodb, table_name):
    """Deletes all items from the specified table.

    Args:
        dynamodb: boto3 DynamoDB object
        table_name: Table we want to retrieve the records from
    """
    items = []

    for item in get_table_items(dynamodb, table_name):
        items.append(
            {
                "DeleteRequest": {
                    "Key": {
                        "AccountId": {"S": item["AccountId"]["S"]},
                        "RuleName": {"S": item["RuleName"]["S"]}
                    }
                }
            }
        )

        if len(items) == MAX_ITEMS:
            response = dynamodb.batch_write_item(RequestItems={table_name: items}, ReturnConsumedCapacity="INDEXES")
            print(response)
            items = []

    # If there are some items still left
    if items:
        response = dynamodb.batch_write_item(RequestItems={table_name: items}, ReturnConsumedCapacity="INDEXES")
        print(response)

def lambda_handler(event, context):
    """Main function.

    Args:
        event: Lambda event
        context: Lambda context
    """
    log_info({"event": event})

    timestamp = datetime.now().isoformat()
    prefix = event.get("prefix", "")
    citizen_account_table = "{}CitizenAccount".format(prefix)
    config_rule_status_table = "{}ConfigRuleStatus".format(prefix)

    sts = boto3.client("sts")
    dynamodb = boto3.client("dynamodb")

    log_info("Deleting all items from {}".format(config_rule_status_table))
    delete_all_items(dynamodb, config_rule_status_table)

    # For each Citizen account
    for citizen_account in get_table_items(dynamodb, citizen_account_table):
        log_info(
            "Getting config rule statuses for account {}".format(citizen_account["AccountId"]["S"])
        )

        import_config_rule_statuses(
            config_rule_status_table,
            citizen_account,
            sts,
            dynamodb,
            timestamp,
            prefix
        )

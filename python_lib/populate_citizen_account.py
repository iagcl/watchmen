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
Populates the CitizenAccount DynamoDB table.
"""
import os
from datetime import datetime

import boto3
import get_accounts

MAX_ITEMS = 25

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

def delete_all_items(dynamodb, table_name):
    """Deletes all items from the specified table.

    Args:
        dynamodb: boto3 DynamoDB object
        table_name: Table we want to retrieve the records from
    """
    items = []

    for item in get_table_items(dynamodb, table_name):
        account_id = item["AccountId"]["S"]
        print "Deleting account {}".format(account_id)

        items.append(
            {
                "DeleteRequest": {
                    "Key": {"AccountId": {"S": account_id}}
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

def main():
    """Populates the CitizenAccount DynamoDB table."""
    prefix = os.environ.get("prefix", "")
    timestamp = datetime.now().isoformat()
    citizen_account_table = "{}CitizenAccount".format(prefix)

    dynamodb = boto3.client("dynamodb", verify=False)

    delete_all_items(dynamodb, citizen_account_table)

    items = []

    for account in get_accounts.get_accounts(False):
        execution_role_arn = "arn:aws:iam::{}:role/{}Citizen".format(account["AccountId"], prefix)

        item = {
            "AccountId": {"S": account["AccountId"]},
            "AccountName": {"S": account["AccountName"]},
            "ExecutionRoleArn": {"S": execution_role_arn},
            "ImportRunTimestamp": {"S": timestamp}
        }

        print "Adding item: " + str(item)

        items.append({"PutRequest": {"Item": item}})

        if len(items) == MAX_ITEMS:
            response = dynamodb.batch_write_item(RequestItems={citizen_account_table: items}, ReturnConsumedCapacity="INDEXES")
            print(response)
            items = []

    # If there are some items still left
    if items:
        response = dynamodb.batch_write_item(RequestItems={citizen_account_table: items}, ReturnConsumedCapacity="INDEXES")
        print(response)

if __name__ == "__main__":
    main()

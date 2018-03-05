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
import datetime
import pytest
import boto3
from mock import patch, Mock

import reports.import_config_rule_status.import_config_rule_status as import_config_rule_status

@pytest.fixture(scope="function")
def _citizen_items_valid():
    return {
        "Items": [
            {
                "AccountId": {"S": "1"},
                "AccountName": {"S": "Account1"},
                "ExecutionRoleArn": {"S": "arn:etc"}
            }
        ]
    }

@pytest.fixture(scope="function")
def _config_rule_status_items_valid():
    return {
        "Items": [
            {
                "AccountId": {"S": "1"},
                "AccountName": {"S": "Account1"},
                "RuleName": {"S": "CheckTags"}
            }
        ]
    }

@pytest.fixture(scope="function")
def _config_rules_comp_valid():
    return {
        "ComplianceByConfigRules": [
            {
                "ConfigRuleName": "Rule1",
                "Compliance": {"ComplianceType": "COMPLIANT"}
            }
        ]
    }

@pytest.fixture(scope="function")
def _config_rules_valid():
    return {
        "ConfigRules": [
            {
                "ConfigRuleName": "Rule1",
                "Source": {
                    "SourceIdentifier": \
                        "arn:aws:lambda:ap-southeast-2:1234567890:function:ProxyLambda"
                }
            }
        ]
    }

@pytest.fixture(scope="function")
def _config_rule_invoke_success():
    return {
        "ConfigRulesEvaluationStatus": [
            {
                "LastSuccessfulInvocationTime": datetime.datetime(2018, 2, 27, 16, 52, 24, 964000, tzinfo=None),
                "FirstEvaluationStarted": True,
                "ConfigRuleName": "CheckConfigRule",
                "ConfigRuleArn": "arn:aws:config:ap-southeast-2:213618447103:config-rule/config-rule-3thzbc",
                "FirstActivatedTime": datetime.datetime(2017, 9, 12, 15, 5, 23, 46000, tzinfo=None),
                "LastSuccessfulEvaluationTime": datetime.datetime(2018, 2, 27, 16, 52, 39, 510000, tzinfo=None),
                "ConfigRuleId": "config-rule-3thzbc"
            }
        ]
    }

@patch("boto3.client")
def test_get_assumed_creds_empty(mock_b3_client):
    assert not import_config_rule_status.get_assumed_creds(boto3.client("sts"), {})

@patch("boto3.client")
def test_get_assumed_creds(mock_b3_client):
    assert import_config_rule_status.get_assumed_creds(
        boto3.client("sts"),
        {"creds": "TestCreds"}
    )

@patch("boto3.client")
def test_get_table_items(mock_b3_client, _citizen_items_valid):
    mock_b3_client("dynamodb").get_paginator("scan").paginate.return_value = [_citizen_items_valid]

    assert import_config_rule_status.get_table_items(boto3.client("dynamobd"), "TestTable")

@patch("boto3.client")
def test_get_config_rules_statuses(mock_b3_client, _config_rules_comp_valid):
    mock_b3_client("config").get_paginator(
        "describe_compliance_by_config_rule"
    ).paginate.return_value = [_config_rules_comp_valid]

    assert import_config_rule_status.get_config_rules_statuses(boto3.client("config"))

@patch("boto3.client")
def test_import_config_rule_statuses(
        mock_b3_client,
        _citizen_items_valid,
        _config_rules_comp_valid,
        _config_rules_valid
    ):
    def mock_get_paginator(arg):
        side_mock = Mock()

        if arg == "describe_compliance_by_config_rule":
            side_mock.paginate.return_value = [_config_rules_comp_valid]
        elif arg == "describe_config_rules":
            side_mock.paginate.return_value = [_config_rules_valid]

        return side_mock

    mock_b3_client("config").get_paginator.side_effect = mock_get_paginator

    assert import_config_rule_status.import_config_rule_statuses(
        "TestTable",
        _citizen_items_valid["Items"][0],
        boto3.client("sts"),
        boto3.client("dynamodb"),
        "",
        ""
    ) is None

@patch("boto3.client")
def test_get_config_rule_invoke_success(mockb3_client, _config_rule_invoke_success):
    mockb3_client("config").describe_config_rule_evaluation_status.return_value = \
        _config_rule_invoke_success
    rule_invocation_time, invocation_result  = import_config_rule_status.get_config_rule_invoke_success(boto3.client("config"),"CheckConfigRule")

    assert invocation_result == "SUCCESS"

@patch("boto3.client")
def test_delete_all_items(mock_b3_client, _config_rule_status_items_valid):
    mock_b3_client("dynamodb").get_paginator("scan").paginate.return_value = \
        [_config_rule_status_items_valid]

    assert import_config_rule_status.delete_all_items(boto3.client("dynamodb"), None) is None

@patch("boto3.client")
@patch("reports.import_config_rule_status.import_config_rule_status.get_table_items")
@patch("reports.import_config_rule_status.import_config_rule_status.delete_all_items")
@patch("reports.import_config_rule_status.import_config_rule_status.get_assumed_creds")
def test_lambda_handler(mock_get_assumed_creds, mock_delete_all_items, mock_get_table_items, mock_b3_client, _citizen_items_valid):
    mock_get_assumed_creds.side_effect = Exception("Test error")
    mock_delete_all_items.return_value = None
    mock_get_table_items.return_value = _citizen_items_valid["Items"]

    assert import_config_rule_status.lambda_handler({}, None) is None

@patch("boto3.client")
def test_get_config_rules_sources(mock_b3_client, _config_rules_valid):
    mock_b3_client("config").get_paginator("describe_config_rules").paginate.return_value = \
        [_config_rules_valid]

    result = import_config_rule_status.get_config_rules_sources(boto3.client("config"))

    assert result["Rule1"] == "arn:aws:lambda:ap-southeast-2:1234567890:function:ProxyLambda"

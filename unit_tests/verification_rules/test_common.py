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

import verification_rules.common.evaluation as evaluation
import verification_rules.common.logger as logger
import verification_rules.common.credential as credential
import verification_rules.common.rule_parameter as rule_parameter

from botocore.stub import Stubber

#################################################################################
# Classes
#################################################################################
class Context(object):
    @property
    def aws_request_id(self):
        return "Req1"

    @property
    def memory_limit_in_mb(self):
        return 1234

    @classmethod
    def get_remaining_time_in_millis(cls):
        return 1234

    @property
    def invoked_function_arn(self):
        return "arn1234"

    @property
    def function_name(self):
        return "FunctionName"

    @property
    def function_version(self):
        return 1

class TestEvaluation(object):
    def test_delete_eval_results_valid(self):
        config = boto3.client("config")

        stubber = Stubber(config)
        stubber.add_response("delete_evaluation_results", {})

        stubber.activate()
        result = evaluation.delete_evaluation_results(config, False, "RuleName") is None
        stubber.deactivate()

        assert result

    def test_delete_eval_results_error(self):
        config = boto3.client("config")

        stubber = Stubber(config)
        stubber.add_client_error("delete_evaluation_results")

        stubber.activate()
        result = evaluation.delete_evaluation_results(config, False, "RuleName") is None
        stubber.deactivate()

        assert result

    def test_put_log_evaluation(self):
        config = boto3.client("config")

        stubber = Stubber(config)
        stubber.add_response("put_evaluations", {})

        stubber.activate()

        eval_elemnt = evaluation.EvaluationElement(
            "resource_id",
            "resource_type",
            "compliance_type",
            "annotation",
            datetime.datetime.now()
        )

        result = evaluation.put_log_evaluation(
            config,
            eval_elemnt,
            "result_token",
            True,
            logger,
            {"resultToken": "resultToken"},
            Context()
        ) is None

        stubber.deactivate()

        assert result

class TestLogger(object):
    def test_log_event(self):
        eval_elemnt = evaluation.EvaluationElement(
            "resource_id",
            "resource_type",
            "compliance_type",
            "annotation",
            "ordering_timestamp"
        )

        result = logger.log_event(
            {"event": "contents", "resultToken": "ResultToken"},
            Context(),
            eval_elemnt,
            "Message"
        ) is None

        assert result

class TestAssumedCredentials(object):
    @pytest.fixture(scope="function")
    def _resp_assume_role_valid(self):
        return {
            "AssumedRoleUser": {
                "AssumedRoleId": "AROAI4WM4ITKVYXUVZ7VQ:RoleId",
                "Arn": "arn:aws:sts::123456789012:assumed-role/TestRole/RoleId"
            },
            "Credentials": {
                "SecretAccessKey": "secretAccessKey",
                "SessionToken": "sessionToken",
                "Expiration": "2017-06-02T03:22:31Z",
                "AccessKeyId": "accessKeyId12345"
            }
        }

    def test_assumed_creds_arn_blank(self):
        assert credential.get_assumed_creds(None, "") == {}

    def test_assumed_creds_arn_missing(self):
        assert credential.get_assumed_creds(None, None) == {}

    def test_assumed_creds_arn_valid(self, _resp_assume_role_valid):
        sts = boto3.client("sts")

        stubber = Stubber(sts)
        stubber.add_response("assume_role", _resp_assume_role_valid)

        stubber.activate()

        assumed_creds = credential.get_assumed_creds(
            sts,
            "arn:aws:iam::123456789012:role/aws-config-role"
        )

        stubber.deactivate()

        assert assumed_creds.get("aws_access_key_id") == "accessKeyId12345"
        assert assumed_creds.get("aws_secret_access_key") == "secretAccessKey"
        assert assumed_creds.get("aws_session_token") == "sessionToken"

class TestEvaluationElement(object):
    def test_instance(self):
        eval_element = evaluation.EvaluationElement(
            "resource_id",
            "resource_type",
            "compliance_type",
            "annotation",
            "ordering_timestamp"
        )

        assert isinstance(eval_element, evaluation.EvaluationElement)

    def test_eval_element_properties(self):
        eval_element = evaluation.EvaluationElement(
            "resource_id",
            "resource_type",
            "compliance_type",
            "annotation",
            "ordering_timestamp"
        )

        assert eval_element.resource_id == "resource_id"
        assert eval_element.resource_type == "resource_type"
        assert eval_element.compliance_type == "compliance_type"
        assert eval_element.annotation == "annotation"
        assert eval_element.ordering_timestamp == "ordering_timestamp"

class TestRuleParameter(object):
    def test_instance_param(self):
        parameter = rule_parameter.RuleParameter({"ruleParameters": '{"testMode": true}'})

        assert isinstance(parameter, rule_parameter.RuleParameter)

    def test_instance_no_param(self):
        parameter = rule_parameter.RuleParameter({})

        assert isinstance(parameter, rule_parameter.RuleParameter)

    def test_get_param(self):
        parameter = rule_parameter.RuleParameter({"ruleParameters": '{"testMode": true}'})

        assert parameter.get("testMode")

    def test_get_no_param(self):
        parameter = rule_parameter.RuleParameter({})

        assert parameter.get("testMode") is None

    def test_get_default_param(self):
        parameter = rule_parameter.RuleParameter({"ruleParameters": '{"testMode": true}'})

        assert parameter.get("missingParam", True)

    def test_get_default_no_param(self):
        parameter = rule_parameter.RuleParameter({})

        assert parameter.get("missingParam", True)


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
import pytest
import boto3

from botocore.stub import Stubber
from verification_rules.common.evaluation import delete_evaluation_results
from verification_rules.common.logger import log_event
from verification_rules.common.credential import get_assumed_creds

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

class EvaluationElement(object):
    @property
    def resource_type(self):
        return "AWS::::Account"

    @property
    def resource_id(self):
        return "1234567890"

    @property
    def compliance_type(self):
        return "COMPLIANT"

    @property
    def annotation(self):
        return "Annotation"

    @property
    def ordering_timestamp(self):
        return ""

class TestEvaluation(object):
    def test_delete_eval_results_valid(self):
        config = boto3.client("config")

        stubber = Stubber(config)
        stubber.add_response("delete_evaluation_results", {})

        stubber.activate()
        result = delete_evaluation_results(config, False, "RuleName") is None
        stubber.deactivate()

        assert result

    def test_delete_eval_results_error(self):
        config = boto3.client("config")

        stubber = Stubber(config)
        stubber.add_client_error("delete_evaluation_results")

        stubber.activate()
        result = delete_evaluation_results(config, False, "RuleName") is None
        stubber.deactivate()

        assert result

class TestLogger(object):
    def test_log_event(self):
        result = log_event({"event": "contents", "resultToken": "ResultToken"}, Context(), EvaluationElement(), "Message") is None

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
        assert get_assumed_creds(None, "") == {}

    def test_assumed_creds_arn_missing(self):
        assert get_assumed_creds(None, None) == {}

    def test_assumed_creds_arn_valid(self, _resp_assume_role_valid):
        sts = boto3.client("sts")

        stubber = Stubber(sts)
        stubber.add_response("assume_role", _resp_assume_role_valid)

        stubber.activate()
        assumed_creds = get_assumed_creds(sts, "arn:aws:iam::123456789012:role/aws-config-role")
        stubber.deactivate()

        assert assumed_creds.get("aws_access_key_id") == "accessKeyId12345" and assumed_creds.get("aws_secret_access_key") == "secretAccessKey" and assumed_creds.get("aws_session_token") == "sessionToken"

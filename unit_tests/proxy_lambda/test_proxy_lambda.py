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
import boto3
from botocore.stub import Stubber
from proxy_lambda.proxy_lambda import invoke_lambda

def test_invoke_lambda():
    b3_lambda = boto3.client("lambda")

    stubber = Stubber(b3_lambda)
    stubber.add_response("invoke", {})

    stubber.activate()

    invoke_lambda(
        b3_lambda,
        {
            "accountId": "123456789012",
            "configRuleName": "ConfigRuleName",
            "resultToken": "resultToken"
        }
    )

    stubber.deactivate()

    assert True

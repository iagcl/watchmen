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

"""Cleans evaluation results"""

import time

def delete_evaluation_results(config, is_test_mode, config_rule_name, sleep_time=1):
    """Deletes evaluation results.

    Args:
        config: (Object) instance of AWS Config client
        is_test_mode: (Boolean)
        config_rule_name: (String) Name of the config rule to clean
        sleep_time: Pause before re-attempting. default is 1 sec.
    """
    if not is_test_mode:
        try:
            config.meta.events._unique_id_handlers['retry-config-config']['handler']._checker.__dict__['_max_attempts'] = 20
            config.delete_evaluation_results(ConfigRuleName=config_rule_name)

        except Exception as exception:
            print "Failed to delete evaluation results. Exception Message: " + exception.message

        # added the sleep to allow the above call to trigger
        # since we had issues when we didn't have it
        time.sleep(sleep_time)

def put_log_evaluation(config, evaluation, result_token, is_test_mode, logger, event, context):
    """Places an element into the evaluation list of the AWS Config rule and logs the information.

    Args:
        config: Instance of AWS Config client
        evaluation: Evaluation element to insert into the Config rule
        result_token: Result token
        is_test_mode: Whether to run in test mode (True/False)
        logger: The object which has the method for logging
        event: Contains the information of the event which was triggered
        context: Context which is passed in from the Lambda function
    """
    logger.log_event(event, context, evaluation, None)

    eval_element = {
        "ComplianceResourceType": evaluation.resource_type,
        "ComplianceResourceId": evaluation.resource_id,
        "ComplianceType": evaluation.compliance_type,
        "OrderingTimestamp": evaluation.ordering_timestamp
    }

    if evaluation.annotation:
        eval_element["Annotation"] = evaluation.annotation

    config.put_evaluations(
        Evaluations=[eval_element],
        ResultToken=result_token,
        TestMode=is_test_mode
    )

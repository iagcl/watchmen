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

"""Logger"""

import json

def log_event(event, context, evaluation, message):
    """Dumps a log of corresponding event in JSON

    Args:
        event: Event
        context: Context
        evaluation: Evaluation parameters
        message: Message
    Returns:
        None
    """
    log = event.copy()
    log.pop("resultToken")

    if context:
        log["requestId"] = context.aws_request_id
        log["memoryLimit"] = context.memory_limit_in_mb
        log["remainingTime"] = context.get_remaining_time_in_millis()
        log["functionArn"] = context.invoked_function_arn
        log["functionName"] = context.function_name
        log["functionVersion"] = context.function_version

    if evaluation:
        log["complianceType"] = evaluation.compliance_type
        log["complianceResourceId"] = evaluation.resource_id
        log["complianceResourceType"] = evaluation.resource_type

        if hasattr(evaluation, "annotation"):
            log["annotation"] = evaluation.annotation

    if message:
        log["message"] = message

    print(json.dumps(log))

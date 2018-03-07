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
Items relating to AWS Config rule parameters.
"""
import json

class RuleParameter(object):
    """Class relating to the AWS Config rule parameters.

    Args:
        event: AWS event payload from AWS Config rule.
    """
    def __init__(self, event):
        if "ruleParameters" in event:
            self._rule_parameters = json.loads(event["ruleParameters"])
        else:
            self._rule_parameters = None

    def get(self, key, default=None):
        """Retrieves the value of the specified key."""
        return default if self._rule_parameters is None else self._rule_parameters.get(key, default)

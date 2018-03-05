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
EvaluationElement class produces an object that is easily consumed by aws config put_evaluations.
"""
import json

class EvaluationElement(object):
    """Produces an object that is easily consumed by aws config put_evaluations.

    Attributes:
        resource_id: AWS resource id
        resource_type: AWS resource type
        compliance_type: "COMPLIANT" or "NON_COMPLIANT"
        annotation: A message for the AWS resource
        ordering_timestamp: The timestamp we want to use
    """
    def __init__(self, resource_id, resource_type, compliance_type, annotation, ordering_timestamp):
        """Inits EvaluationElement class."""
        self._resource_id = resource_id
        self._resource_type = resource_type
        self._compliance_type = compliance_type
        self._annotation = annotation
        self._ordering_timestamp = ordering_timestamp

    @property
    def resource_id(self):
        """Returns resource id."""
        return self._resource_id

    @property
    def resource_type(self):
        """Returns resource type."""
        return self._resource_type

    @property
    def compliance_type(self):
        """Returns compliance type 'COMPLIANT' or 'NON_COMPLIANT'."""
        return self._compliance_type

    @property
    def annotation(self):
        """Returns annotation."""
        return self._annotation

    @property
    def ordering_timestamp(self):
        """Returns ordering timestamp."""
        return self._ordering_timestamp

    def to_json(self):
        """Returns json object."""
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

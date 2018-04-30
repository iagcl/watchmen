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
CloudTrail class that checks if cloudtrail is configured correctly
"""
class CloudTrail(object):
    """Retrieves CloudTrail information and uses it accordingly.

    Args:
        b3_cloudtrail: boto3 cloudtrail client
    """
    def __init__(self, b3_cloudtrail):
        self._trails = b3_cloudtrail.describe_trails(
            trailNameList=[],
            includeShadowTrails=False
        )["trailList"]

        self._trail_statuses = {}
        self._event_selectors = {}

        for trail in self._trails:
            self._trail_statuses[trail["Name"]] = b3_cloudtrail.get_trail_status(Name=trail["Name"])

            self._event_selectors[trail["Name"]] = b3_cloudtrail.get_event_selectors(
                TrailName=trail["Name"]
            )["EventSelectors"]

    @property
    def is_settings_correct(self):
        """
        Make sure that the aws cloudtrail is configured correctly
        """
        # if there are no CloudTrail trails configured
        if not self._trails:
            return False

        is_config_correct = False

        # get details for each trail
        for trail in self._trails:
            trail_status = self._trail_statuses.get(trail["Name"])

            # if logging is off
            if not trail_status["IsLogging"]:
                continue

            # if "Apply trail to all regions" is not set to Yes
            if not trail["IsMultiRegionTrail"]:
                continue

            event_selectors = self._event_selectors.get(trail["Name"])

            # if Read/Write events is not All
            if event_selectors[0]["ReadWriteType"] != "All":
                continue

            # if S3 Bucket does not exist
            if not trail["S3BucketName"]:
                continue

            # if "Encrypt log files" is set
            if "KmsKeyId" in trail:
                continue

            # if "Enable log file validation" is not set
            if not trail["LogFileValidationEnabled"]:
                continue

            # this trail is valid
            is_config_correct = True
            break

        return is_config_correct

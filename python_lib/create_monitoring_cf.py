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
Creates the proxy lambda CloudFormation template.
"""
import common
import get_notifications
import os

RULE_TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/templates/monitoring.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/files/monitoring.yml"

def main():
    """Main function"""
    template = common.get_template(RULE_TEMPLATE_BASE).replace(
        "{{notifications_slack}}",
        get_notifications.get_notification_slack()
    ).replace(
        "{{slack_channel_hook_url}}",
        get_notifications.get_slack_channel_hook_url()
    ).replace(
        "{{notifications_email}}",
        get_notifications.get_notification_email()
    )

    common.generate_file(TEMPLATE_DESTINATION, template)

if __name__ == "__main__":
    main()

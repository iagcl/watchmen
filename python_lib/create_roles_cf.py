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
import common
import get_accounts
import os

TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/templates/roles.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/files/roles.yml"

def main():
    roles_cf = common.get_template(TEMPLATE_BASE)
    common.generate_file(TEMPLATE_DESTINATION, roles_cf) # Creates the deployable CF file

if __name__ == "__main__":
    main()

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
from common import get_temp, generate_file
from get_accounts import get_accounts

TEMP_BASE = "watchmen_cloudformation/templates/roles.tmpl"
TEMP_DESTINATION = "watchmen_cloudformation/files/roles.yml"

def get_citizen_roles(accounts):
    citizen_roles = ""
    for account in accounts:
        if citizen_roles != "":
            citizen_roles += "\n"

        citizen_roles += "{}- !Sub \"arn:aws:iam::{}:role/{}Citizen\"".format(" " * 14, account, "${Prefix}")

    return citizen_roles

def get_citizen_update_roles(accounts):
    citizen_update_roles = ""
    for account in accounts:
        if citizen_update_roles != "":
            citizen_update_roles += "\n"

        citizen_update_roles += "{}- !Sub \"arn:aws:iam::{}:role/{}CitizenUpdate\"".format(" " * 14, account, "${Prefix}")

    return citizen_update_roles

def main():
    roles_cf = get_temp(TEMP_BASE).replace( # Update Citizen roles with Citizen account info
        "{{citizen_roles}}",
        get_citizen_roles(get_accounts())
    ).replace( # Update CitizenUpdate roles with Citizen account info
        "{{citizen_update_roles}}",
        get_citizen_update_roles(get_accounts())
    )
    generate_file(TEMP_DESTINATION, roles_cf) # Creates the deployable CF file

if __name__ == "__main__":
    main()

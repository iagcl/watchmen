
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
import os

from os import listdir
from os.path import isdir, join

VERIFICATION_RULES_FOLDER = os.environ["LOCATION_CORE"] + "/verification_rules"
EXCLUDED_FOLDERS = ["common"]

def get_rules_raw(rules_location=[VERIFICATION_RULES_FOLDER]):
    result = []
    master_excluded_folders = EXCLUDED_FOLDERS

    directories = []

    # Get a list of rule names from the various rules locations
    for rule_loc in rules_location:
        directories += listdir(rule_loc)

    for directory in directories:
        for rules_loc in rules_location:
            if isdir(join(rules_loc, directory)) and directory not in master_excluded_folders:
                result.append(directory)
                break

    return result

def get_rules(rules_location=[VERIFICATION_RULES_FOLDER]):
    rules = []

    for rule in get_rules_raw(rules_location):
        rules.append(
            {
                'name': rule,
                'environment': get_environment(rules_location, rule),
                'description': get_description(rules_location, rule)
            }
        )

    return rules

# Method to read environment variables from lambda functions if applicable & return a json with '{env_var:value}'. The environment variable should be passed in docker.
# To pass multiple environment variables to Lambda use "ENVIRONMENT_VARIABLES: var1,var2,var3" in the lambda python file e.g. check_citizen_version.py

def get_environment(rules_location, rule):
    filer = _get_rule_path_filename(rules_location, rule)

    with open(filer, 'r') as file_content:
        for line in file_content:
            if 'ENVIRONMENT_VARIABLES:' in line:
                env_vars = {}

                environment_variables = line.rstrip().replace(' ', '').replace(
                    "ENVIRONMENT_VARIABLES:",
                    ""
                )

                if "," in environment_variables:
                    environment_variables = environment_variables.split(',')
                else:
                    # Convert the string to a list
                    environment_variables = [environment_variables]

                for environment_variable in environment_variables:
                    if environment_variable in os.environ:
                        # Create json with '{environment_variable:environment_variable_value}'
                        env_vars[environment_variable] = os.environ[environment_variable]

                return env_vars

        return {}

def get_description(rules_location, rule):
    filer = _get_rule_path_filename(rules_location, rule)

    with open(filer, 'r') as file_content:
        for line in file_content:
            if 'RULE_DESCRIPTION:' in line:
                return line.rstrip().replace("RULE_DESCRIPTION: ", "")

    raise Exception('Rule ' + rule + ' needs a RULE_DESCRIPTION value')

def _get_rule_path_filename(rules_location, rule):
    """Gets the path and filename of the verifucation rule.

    Args:
        rules_location: List of rules locations
        rule: Rile name

    Returns:
        Path and filename of the verifucation rule
    """
    path_filename = ""

    for rules_loc in rules_location:
        path_filename = join(rules_loc, rule, rule + ".py")

        if os.path.isfile(path_filename):
            break

    return path_filename


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
from os import listdir
from os.path import isdir, join
import os
import json

VERIFICATION_RULES_FOLDER = "./verification_rules"
EXCLUDED_FOLDERS = ["common"]

def get_rules_raw():
    return [
        f for f in listdir(VERIFICATION_RULES_FOLDER)
        if isdir(join(VERIFICATION_RULES_FOLDER, f)) and f not in EXCLUDED_FOLDERS
    ]

def get_rules():
    return reduce(get_rule, get_rules_raw(), [])

def get_rule(rules, rule):
    rules.append({
        'name': rule,
        'environment': get_environment(rule),
        'description': get_description(rule)
    })
    return rules

# Method to read environment variables from lambda functions if applicable & return a json with '{env_var:value}'. The environment variable should be passed in docker.
# To pass multiple environment variables to Lambda use "ENVIRONMENT_VARIABLES: var1,var2,var3" in the lambda python file e.g. check_citizen_version.py

def get_environment(rule):
    file = join(VERIFICATION_RULES_FOLDER, rule, rule + ".py")
    with open(file, 'r') as input:
        for line in input:
            if 'ENVIRONMENT_VARIABLES:' in line:
                environment_variables = line.rstrip().replace(' ','').replace("ENVIRONMENT_VARIABLES:", "")
                env_var_list = {}
                environment_variables = environment_variables.split(',') if "," in environment_variables else environment_variables
                if type(environment_variables)==list:
                    for environment_variable in environment_variables:
                        if environment_variable in os.environ:
                            environment_variable_value = os.environ[environment_variable]
                            env_var_list[environment_variable] = environment_variable_value  # Create json with '{environment_variable:environment_variable_value}'
                            env_list_json = json.dumps(env_var_list)
                        else:
                            env_list_json = json.dumps(env_var_list)
                    return env_list_json
                elif type(environment_variables)==str:
                    if environment_variables in os.environ:
                        environment_variable_value = os.environ[environment_variables]
                        env_var_list[environment_variables] = environment_variable_value
                        env_list_json = json.dumps(env_var_list)
                        return env_list_json
                else:
                    return '{}'
        return '{}'

def get_description(rule):
    file = join(VERIFICATION_RULES_FOLDER, rule, rule + ".py")
    with open(file, 'r') as input:
        for line in input:
            if 'RULE_DESCRIPTION:' in line:
                return line.rstrip().replace("RULE_DESCRIPTION: ", "")
    raise Exception('Rule ' + rule + ' needs a RULE_DESCRIPTION value')
    # return "Rule Description"

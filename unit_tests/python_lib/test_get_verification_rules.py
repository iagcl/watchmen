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
import python_lib.get_verification_rules as verification_rules

RULES_LOCATION = [os.environ["LOCATION_CORE"] + "/verification_rules"]

def test_get_rules_raw_default():
    assert verification_rules.get_rules_raw()

def test_get_rules_raw_true():
    assert verification_rules.get_rules_raw()

def test_get_rules():
    assert verification_rules.get_rules()

def test_get_environment():
    os.environ["BUCKET_NAME_DISTRIBUTION"] = "test_bucket"
    result = verification_rules.get_environment(RULES_LOCATION, "check_citizen_version")
    os.environ.pop("BUCKET_NAME_DISTRIBUTION")

    assert result

def test_get_description():
    assert verification_rules.get_description(RULES_LOCATION, "check_citizen_version")

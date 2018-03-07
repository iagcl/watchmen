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
#!/bin/bash
rm -rf $LOCATION_CORE/*.cid
rm -rf $LOCATION_CORE/unit_tests/__pycache__
rm -rf $LOCATION_CORE/integration_tests/__pycache__
rm -rf $LOCATION_CORE/env/
rm -rf $LOCATION_CORE/htmlcov/
rm -rf $LOCATION_CORE/zip_files/
rm -rf $LOCATION_CORE/pylint/
rm -rf $LOCATION_CORE/watchmen.egg-info/
rm -rf $LOCATION_CORE/watchmen_cloudformation/files/
rm -rf $LOCATION_CORE/citizen_cloudformation/files/citizen-rules-cfn.yml*

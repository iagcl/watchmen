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
from verification_rules.check_citizen_version.check_citizen_version import get_citizen_stacks

_single_citizen_stack = [
    {
        'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/Citizen/7851f78f-c79e-4a9a-b9e9-0d975f18f8de',
        'Description': 'Watchmen-Citizen Compliance Rules Version XXX-CITIZEN-VERSION-XXX',
        'StackName': 'Citizen'
    }
]

_multiple_stacks_one_citizen = [
    {
        'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/Citizen/7851f78f-c79e-4a9a-b9e9-0d975f18f8de',
        'Description': 'Watchmen-Citizen Compliance Rules Version XXX-CITIZEN-VERSION-XXX',
        'StackName': 'Citizen'
    },
    {
        'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/SomeOtherStack/8a972533-dadc-4a75-adae-fcd03e05d31d',
        'Description': 'This is some other stack, it does something else',
        'StackName': 'SomeOtheStack'
    }
]

_multiple_stacks_no_citizens = [
    {
        'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/SomeOtherStack/8a972533-dadc-4a75-adae-fcd03e05d31d',
        'Description': 'This is some other stack, it does something else',
        'StackName': 'SomeOtheStack'
    },
    {
        'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/AnotherStack/fa1f317f-610b-4d7c-a8fa-5c40f515fb56',
        'Description': 'This is another stack',
        'StackName': 'AnotherStack'
    }
]

_no_stacks = []

class TestCheckCitizenVersion(object):

    def test_single_citizen_stacks(self):
        stacks = _single_citizen_stack
        citizen_stacks = get_citizen_stacks(stacks)
        assert citizen_stacks == [
            {
                'StackName': 'Citizen',
                'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/Citizen/7851f78f-c79e-4a9a-b9e9-0d975f18f8de',
                'Version': 'XXX-CITIZEN-VERSION-XXX'
            }
        ]

    def test_multiple_stacks(self):
        stacks = _multiple_stacks_one_citizen
        citizen_stacks = get_citizen_stacks(stacks)
        assert citizen_stacks == [
            {
                'StackName': 'Citizen',
                'StackId': 'arn:aws:cloudformation:ap-southeast-2:1234567890:stack/Citizen/7851f78f-c79e-4a9a-b9e9-0d975f18f8de',
                'Version': 'XXX-CITIZEN-VERSION-XXX'
            }
        ]

    def test_multiple_stacks_no_citizens(self):
        stacks = _multiple_stacks_no_citizens
        citizen_stacks = get_citizen_stacks(stacks)
        assert citizen_stacks == []

    def test_no_stacks(self):
        stacks = _no_stacks
        citizen_stacks = get_citizen_stacks(stacks)
        assert citizen_stacks == []

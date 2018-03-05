
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
import re

def generate_file(file_path, content):
    path = os.path.dirname(file_path)

    # if the path does not exist, create it
    if not os.path.exists(path):
        os.makedirs(path)

    # remove the file if it exists
    if os.path.exists(file_path):
        print "Removing \"{}\"".format(file_path)
        os.remove(file_path)

    with open(file_path, "w") as filer:
        filer.write(content)

def to_pascal_case(snake_str):
    components = snake_str.split('_')
    return "".join(x.title() for x in components)

def to_snake_case(name):
    str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()

def get_template(template_base):
    template = ""
    with open(template_base) as filer:
        template = filer.read()
    return template

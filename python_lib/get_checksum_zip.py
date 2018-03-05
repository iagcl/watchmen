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

ZIP_FOLDER = os.environ['LOCATION_CORE']+ "/zip_files"

def get_checksum_zip(file_name):
    zip_files = [
        f for f in listdir(ZIP_FOLDER)
        if f.endswith(".zip")
    ]
    return find_checksum_zip_file_name(file_name, zip_files)

def find_checksum_zip_file_name(file_name, zip_files):
    if zip_files:
        return next(f for f in zip_files if file_name in f)
    else:
        return ""
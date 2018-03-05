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
import zipfile
import checksumdir

VERIFICATION_RULES_FOLDER = "./verification_rules"
ZIP_FILES_FOLDER = "./zip_files/"
EXCLUDED_FOLDERS = ["common"]

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_root = '.' + root.replace(path, "")
            filename = os.path.join(root, file)
            ziph.write(filename, os.path.join(file_root, file))

def get_child_folders(parent_folder):
    return [
        f for f in os.listdir(parent_folder)
        if os.path.isdir(os.path.join(parent_folder, f)) and f not in EXCLUDED_FOLDERS
    ]

def get_checksum(folder, zip_f):
    file = os.path.join(zip_f, folder)
    return checksumdir.dirhash(file)

def zip_folder(parent_folder, child_folder, checksum):
    file_from = os.path.join(parent_folder, child_folder)
    file_to = os.path.join(ZIP_FILES_FOLDER, child_folder + '.' + checksum + '.zip')
    zipf = zipfile.ZipFile(file_to, 'w', zipfile.ZIP_DEFLATED)
    zipdir(file_from, zipf)
    zipf.close()

def zip_folders(parent_folder):
    for child_folder in get_child_folders(parent_folder):
        zip_folder(
            parent_folder,
            child_folder,
            get_checksum(child_folder, parent_folder)
        )

def main():
    zip_folders("./verification_rules")
    zip_folders(os.environ['LOCATION_CORE']+"/reports")
    zip_folders(os.environ['LOCATION_CORE']+"/citizen_updates")
    zip_folders(os.environ['LOCATION_CORE']+"/elasticsearch")

if __name__ == "__main__":
    main()

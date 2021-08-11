import json
import os


def read_json_file(filename):
    with open(filename, "r") as file:
        jsonStr = file.read()
        dict = json.loads(jsonStr)
    return dict


def write_json_file(folder, filename, dict):
    jsonStr = json.dumps(dict)
    if not os.path.isdir(folder):
        os.mkdir(folder)
    full_filename = f'{folder}/{filename}'
    with open(full_filename, "w") as file:
        file.write(jsonStr)

import array
import json
import os, sys, subprocess
import tempfile
from time import process_time

from reefscanner.basic_model.json_utils import read_json_file
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops


def survey_id_parts(survey_id: str):
    start_index = 0
    parts = []
    while True:
        underscore = survey_id.find("_", start_index)
        if underscore == -1:
            parts.append(survey_id[start_index:])
            break
        parts.append(survey_id[start_index:underscore])
        start_index = underscore + 1

    no_parts = len(parts)
    parts_dict={}
    if no_parts > 0:
        parts_dict["seq"] = parts[no_parts-1]
    if no_parts > 1:
        parts_dict["time"] = parts[no_parts-2]
    if no_parts > 2:
        parts_dict["date"] = parts[no_parts-3]
    if no_parts > 3:
        device_id = ""
        sep = ""
        for p in range(0, no_parts -3):
            device_id = f"{device_id}{sep}{parts[p]}"
            sep = "_"
        parts_dict["device_id"] = device_id

    return parts_dict

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


# read a json file from local disk or from a samba drive
def read_json_file_support_samba(file, samba: bool):
    ops = get_file_ops(samba)
    if ops.exists(file):
        if samba:
            with tempfile.TemporaryDirectory() as folder:
                fname = f"{folder}\\survey.json"
                ops.copyfile(file, fname)
                survey_json = read_json_file(fname)
        else:
            survey_json = read_json_file(file)
    else:
        survey_json = {}
    return survey_json


# read a binary file from local disk or from a samba drive
def read_binary_file_support_samba(file, samba: bool) -> bytes:
    ops = get_file_ops(samba)
    if ops.exists(file):
        if samba:
            with tempfile.TemporaryDirectory() as folder:
                fname = f"{folder}\\survey.json"
                ops.copyfile(file, fname)
                contents = read_binary_file(fname)
        else:
            contents = read_binary_file(file)
    else:
        raise Exception(f"File not found {file}")
    return contents


# read a binary file from local disk
def read_binary_file(file) -> bytes:
    filebytes = array.array('b')
    with open(file, 'rb') as fileR:

        filebytes.frombytes(fileR.read())

    return bytes(filebytes)

def write_json_file(filename, dict):
    jsonStr = json.dumps(dict)
    with open(filename, "w") as file:
        file.write(jsonStr)

def is_empty_folder(path):
    if not os.path.exists(path):
        return True
    try:
        with os.scandir(path) as it:
            if any(it):
                return False
    except:
        return True

    return True

if __name__ == "__main__":
    print(survey_id_parts("REEFSCAN_09_20240507_051927_Seq01"))

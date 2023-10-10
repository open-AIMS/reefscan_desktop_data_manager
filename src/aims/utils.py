import array
import os, sys, subprocess
import tempfile

from reefscanner.basic_model.json_utils import read_json_file
from reefscanner.basic_model.samba.file_ops_factory import get_file_ops


def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


# search s for the last occurence of old and replace with with new
def replace_last(s: str, old: str, new: str):
    return new.join(s.rsplit(old, 1))


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
        contents = None
    return contents


# read a binary file from local disk
def read_binary_file(file) -> bytes:
    filebytes = array.array('b')
    with open(file, 'rb') as fileR:
        filebytes.frombytes(fileR.read())

    return bytes(filebytes)

import os
from typing import List

from reefscanner.basic_model.json_utils import read_json_file

from aims.ccip.tow import Tow


class Tows():
    def __init__(self, tow_folder):

        self.tows:List[Tow] = []
        f = os.listdir(tow_folder)
        print (f)
        sub_folders = os.listdir(tow_folder)
        for sub_folder in sub_folders:
            full_sub_folder = f"{tow_folder}/{sub_folder}"
            if os.path.isdir(full_sub_folder):
                full_sub_folder = f"{tow_folder}/{sub_folder}"
                files = [name for name in os.listdir(full_sub_folder) if name.lower().endswith(".json")]
                for file in files:
                    full_file = f"{full_sub_folder}/{file}"
                    self.read_json_file(full_file)

        self.tows = sorted(self.tows, key=lambda d: d.time)
        self.cur_index: int = 0

    def read_json_file(self, file):
        tows_json = read_json_file(file)
        for dict in tows_json:
            tow = Tow(dict)
            self.tows.append(tow)

    def first(self):
        self.cur_index = 0
        return self.cur()

    def cur(self):
        if self.cur_index >= len(self.tows):
            return None
        else:
            return self.tows[self.cur_index]

    def next(self):
        self.cur_index+=1
        return self.cur()

    def dicts(self):
        dicts = []
        for tow in self.tows:
            dicts.append(tow.dict())
        return dicts

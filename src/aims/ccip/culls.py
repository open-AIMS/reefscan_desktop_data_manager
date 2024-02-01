import os
from typing import List

from reefscanner.basic_model.json_utils import read_json_file

from aims.ccip.cull import Cull



class Culls():
    def __init__(self, cull_folder):

        self.culls = {}
        f = os.listdir(cull_folder)
        print (f)
        sub_folders = os.listdir(cull_folder)
        for sub_folder in sub_folders:
            full_sub_folder = f"{cull_folder}/{sub_folder}"
            if os.path.isdir(full_sub_folder):
                full_sub_folder = f"{cull_folder}/{sub_folder}"
                files = [name for name in os.listdir(full_sub_folder) if name.lower().endswith(".json")]
                for file in files:
                    full_file = f"{full_sub_folder}/{file}"
                    self.read_json_file(full_file)


        self.cur_index: int = 0

    def read_json_file(self, file):
        culls_json = read_json_file(file)
        for dict in culls_json:
            cull = Cull(dict)
            culls_for_poly = self.culls.get(cull.name)
            if culls_for_poly is None:
                culls_for_poly = []
            culls_for_poly.append(cull)
            self.culls[cull.name] = culls_for_poly

    def first(self):
        self.cur_index = 0
        return self.cur()

    def cur(self):
        if self.cur_index >= len(self.culls):
            return None
        else:
            return self.culls[self.cur_index]

    def next(self):
        self.cur_index+=1
        return self.cur()


import os


class BenthicPoint():
    def __init__(self, dict):
        self.photo = os.path.basename(dict["image_path"])
        self.point = dict["point_id"]
        self.group = dict["pred_group"]
# serialize and de-serialize to dicts

def de_serialize_proportional_rectangle(dict):
    return ProportionalRectangle(dict["left"],
                                 dict["top"],
                                 dict["width"],
                                 dict["height"],
                                 dict["sequence_id"],
                                 dict["phantom"]
                                 )


def de_serialize_proportional_rectangle_lookup(lookup: dict):
    return_lookup = {}
    for key in lookup.keys():
        list = lookup[key]
        return_list = []
        for dict in list:
            return_list.append(de_serialize_proportional_rectangle(dict))

        return_lookup[key] = return_list

    return return_lookup


def serialize_proportional_rectangle_lookup(lookup):
    return_lookup = {}
    for key in lookup.keys():
        list = lookup[key]
        return_list = []
        for proportional_rectangle in list:
            return_list.append(proportional_rectangle.serialize())
        return_lookup[key]= return_list

    return return_lookup


# stores the location of a detected COTS within a photo
# the numbers a proportional to the size of the photo
class ProportionalRectangle:
    def __init__(self, left: str, top: str, width: str, height: str, sequence_id: str, phantom=False):
        self.left = float(left)
        self.top = float(top)
        self.width = float(width)
        self.height = float(height)
        self.sequence_id = sequence_id
        self.phantom = phantom

    def serialize(self):
        return {
            "sequence_id": self.sequence_id,
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
            "phantom": self.phantom

        }

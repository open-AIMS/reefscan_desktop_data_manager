def deserialize_image_with_score(dict):
    return ImageWithScore(dict["path"], dict["score"])

class ImageWithScore:
    def __init__(self, path, score):
        self.path = path
        self.score = score


    def serialize(self):
        return {
            "path": self.path,
            "score": self.score
        }
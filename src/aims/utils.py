# search s for the last occurence of old and replace with with new
def replace_last(s: str, old: str, new: str):
    return new.join(s.rsplit(old, 1))
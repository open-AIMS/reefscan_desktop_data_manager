import os, sys, subprocess


def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


# search s for the last occurence of old and replace with with new
def replace_last(s: str, old: str, new: str):
    return new.join(s.rsplit(old, 1))

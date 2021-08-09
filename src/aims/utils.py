import json

def readJsonFile(filename):
    with open(filename, "r") as file:
        jsonStr = file.read()
        dict = json.loads(jsonStr)
    return dict

def writeJsonFile(filename, dict):
    jsonStr = json.dumps(dict)
    with open(filename, "w") as file:
        file.write(jsonStr)


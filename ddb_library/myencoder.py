import json

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__
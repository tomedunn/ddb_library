import json
from .myencoder import MyEncoder

class ContentReference:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        self.name = d.get('name', None)
        self.type = d.get('type', None)
        self.id = d.get('id', None)
        self.modified = d.get('modified', None)
        self.path = d.get('path', None)
        self.sources = d.get('path', [])
        self.html = d.get('html', None)

    def __repr__(self):
        return f'{self.__dict__}'
    
    def get_html( self ):
        return self.html
    
    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
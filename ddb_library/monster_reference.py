from bs4 import BeautifulSoup
import json
from .myencoder import MyEncoder
import re

class MonsterReference:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        self.name = d.get('name', None)
        self.id = d.get('id', None)
        self.modified = d.get('modified', None)
        self.path = d.get('path', None)
        self.sources = d.get('path', [])
        self.html = d.get('html', None)

    def __repr__(self):
        return f'{self.__dict__}'
    
    def get_html( self ):
        if self.html: return self.html
        
        def _monster_class( class_ ):
            re_monster = re.compile(
                r'^(?:'
                    r'Basic-Text-Frame(-\d)?'
                    r'|monster--stat-block'
                    r'|stat-block'
                r')$'
            )
            return class_ and re_monster.match(class_)
        
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin.read(), 'html.parser')

        for d in soup.find_all('div', class_=_monster_class):
            p = d.find(['h3','p'], {'class': 'Stat-Block-Styles_Stat-Block-Title'})
            if not p: 
                p = d.find(['h2','h3','h4','h5'], {'class': 'heading-anchor'})

            if not p: continue

            a = p.find('a', {'class': 'tooltip-hover monster-tooltip'})
            if not a: continue
            if a['href'][10:] != self.id: continue

            #a = d.find('a', {'class': 'ddb-lightbox-outer monster-image-center'})
            #if a: a.decompose()

            return str(d)

        return None
    
    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
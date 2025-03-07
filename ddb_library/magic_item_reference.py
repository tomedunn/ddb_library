from bs4 import BeautifulSoup
import json
from .myencoder import MyEncoder

class MagicItemReference:
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
    
    def get_html(self, **kwargs):
        if self.html:
            return self.html
        
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin, 'html.parser')
        
        # find all spells within the page
        for h in soup.find_all('h3'):
            a = h.find('a', {'class': 'tooltip-hover magic-item-tooltip'})
            if not a: continue

            if a['href'][8:] != self.id:
                continue

            # extract all lines between this <h3> and the next one
            s = BeautifulSoup(str(h), 'html.parser')
            for n in h.find_next_siblings():
                if n.name in ['h1','h2','h3']:
                    break
                elif len(n.get_text('', strip=True)) > 0:
                    s.append('\n')
                    s.append(n)
            
            return str(s)

        return None
    
    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
from .content import *
from bs4 import BeautifulSoup
import re
import uuid


class Treasure(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.book_path = kwargs.get('book_path', None)
        self.treasure = kwargs.get('treasure', [])
        self.html = kwargs.get('html', None)
        if self.html: self.__process_html()

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Treasure',
            'id': self.id,
            'book_path': self.book_path,
            'treasure': self.treasure,
        }

    def __process_html(self):
        TEXT_TO_NUMBER = {
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5,
            'six': 6,
            'seven': 7,
            'eight': 8,
            'nine': 9,
            'ten': 10,
            'eleven': 11,
            'twelve': 12,
            'dozen': 12,
            'thirteen': 13,
            'fourteen': 14,
            'fifteen': 15,
            'sixteen': 16,
            'seventeen': 17,
            'eighteen': 18,
            'nineteen': 19,
            'twenty': 20,
            '.': 1,
        }

        soup = BeautifulSoup(self.html, 'html.parser')
        treasure = []
        number = 1
        for tag in soup.contents:
            if not tag.name: continue
            for c in tag.contents:
                if c.name == 'a':
                    if 'magic-item-tooltip' in c.get('class', []): 
                        id = c['href'].split('/')[-1]
                        if not re.match(r'^(?P<id_num>\d+)-.*$', id): continue
                        treasure += [(number, f'magic-items/{id}')]
                        number = 1
                    elif 'item-tooltip' in c.get('class', []): 
                        id = c['href'].split('/')[-1]
                        if not re.match(r'^(?P<id_num>\d+)-.*$', id): continue
                        treasure += [(number, f'equipment/{id}')]
                        number = 1
                elif not c.name:
                    for m in re.finditer(
                            r'\b(?:' 
                                r'(?P<money>\d[\d,]* [CSGEP]P)'
                                r'|(?P<time>\b\d+ (?:days|minutes|hours)\b)'
                                r'|(?P<test>\bDC \d+\b)'
                                r'|(?P<period>\.)'
                                r'|(?P<number>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)'
                            r')\b', c.get_text('', strip=False), re.IGNORECASE):
                        if m['money']:
                            treasure += [(number, m['money'])]
                        elif m['period']:
                            number = 1
                        elif m['number']:
                            number = m['number'].lower()
                            if re.match(r'\d+', number):
                                number = int(number)
                            else:
                                number = TEXT_TO_NUMBER.get(number, 1)
                

                else:
                    pass

        self.treasure = treasure
        
    def contents(self):
        """
        Returns a list of all items and gold in the treasure.

        Returns
        ----------
        treasure : list
            The individual contents in the treasure.
        """
        treasure = []
        for t in self.treasure:
            treasure.extend(t[0]*[t[1]])
        
        return treasure

    def gold(self):
        """
        Returns the total gold in the treasure.

        Returns
        ----------
        gold : float
            The equivalent gold value of all coins in the treasure.
        """
        COIN_TO_GP = {
            'PP': 10.0,
            'GP': 1.0,
            'EP': 0.2,
            'SP': 0.1,
            'CP': 0.01,
        }
        gold = 0
        for n, t in self.treasure:
            if t.startswith('magic-items'): continue
            if t.startswith('equipment'): continue

            v, c = t.split(' ')
            v = float(v.replace(',',''))*COIN_TO_GP[c]
            gold += n*v

        return gold
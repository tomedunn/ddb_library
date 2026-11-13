from .content import *
from .figure import Figure
from .list import List
from .monster import Monster
from .table import Table
from bs4 import BeautifulSoup
import re

class MagicItem(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.type = kwargs.get('type', None)
        self.subtype = kwargs.get('subtype', None)
        self.rarity = kwargs.get('rarity', None)
        self.attunement = kwargs.get('attunement', None)
        self.description = kwargs.get('description', [])
        for line in self.description:
            if type(line) is dict:
                if line['content_type'] == 'List':
                    line = List(**line)
                elif line['content_type'] == 'Monster':
                    line = Monster(**line)
                elif line['content_type'] == 'Table':
                    line = Table(**line)
        self.figure = kwargs.get('figure', None)
        if type(self.figure) is dict: self.figure = Figure(**self.figure)
        self.html = kwargs.get('html', None)
        if self.html: self.__process_html()

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Magic Item',
            'id': self.id,
            'name': self.name,
            'book_path': self.book_path,
            'url': self.url,
            'type': self.type,
            'subtype': self.subtype,
            'rarity': self.rarity,
            'attunement': self.attunement,
            'description': [d if type(d) is str else d.to_dict() for d in self.description],
            'figure': self.figure.to_dict() if self.figure else None,
        }

    def __process_html(self):
        def process_figure(soup):
            figure = {}
            t = soup.find('span', class_='artist-credit')
            if t: figure['artist'] = t.get_text()
        
            t = soup.find('img')
            if t: figure['src'] = t['src']
        
            t = soup.find('figcaption')
            if t: figure['caption'] = t.get_text()

            if figure:
                return Figure(
                    book_path=self.book_path,
                    url=self.url,
                    **figure,
                )
            else:
                return None
        
        soup = BeautifulSoup(self.html.replace('\n',''), 'html.parser')

        # header
        tag = soup.contents[0]
        a = tag.find('a', {'class': 'tooltip-hover magic-item-tooltip'})
        if a:
            self.id = a['href'].split('/')[-1]
            self.name = a.get_text('', strip=True)
        tag = tag.next_sibling

        # skip figure for now
        if tag.name in ['figure']:
            tag = tag.next_sibling
        
        # meta data
        m = re.match(
            r'\b(?P<type>armor|potion|ring|rod|scroll|staff|wand|weapon|wondrous item)\b\s*'
            r'(?:\((?P<subtype>[^\)]+)\))?,\s*'
            r'\b(?P<rarity>common|uncommon|rare|very rare|legendary|artifact|rarity [\w\s]+|varies)\b\s*'
            r'(?:\((?P<attunement>requires attunement)\))?',
            tag.get_text('', strip=True),
            re.IGNORECASE
        )
        if m:
            self.type = m['type']
            self.subtype = m.group('subtype')
            self.rarity = m['rarity']
            self.attunement = m.group('attunement')

        # description
        description = []
        for e in tag.find_next_siblings(['div','ol','p','ul','li','table']):
            if e.name == 'p':
                description.append(e.get_text().strip())
            elif e.name == 'li':
                print(str(e))
            elif e.name == 'div':
                description.append(Monster(**{
                    'content_type': 'Monster',
                    'book_path': self.book_path,
                    'url': self.url,
                    'html': str(e),
                }))
            elif e.name in ['ol','ul']:
                description.append(List(**{
                    'content_type': 'List',
                    'book_path': self.book_path,
                    'url': self.url,
                    'html': str(e),
                }))
            elif e.name == 'table':
                description.append(Table(**{
                    'content_type': 'Table',
                    'book_path': self.book_path,
                    'url': self.url,
                    'html': str(e),
                }))
        
        self.description = description

        # figure
        self.figure = process_figure(soup)

    def to_str(self):
        """
        Converts the magic item to a plain text string.

        Parameters
        ----------
        rules : str
            Determines how the magic item is formatted, either ``'2014'`` or ``'2024'``. 
            If ``'2014'`` the stat block will be formatted to match magic items published under the 2014 rules (5e), 
            and if ``'2024'`` the format will match those published under the 2024 rules (5.5e).
            Default value ``'2024'``.
        
        Returns
        -------
        text : str
            Plain text magic item.
        """
        pt = []
        
        # name
        pt.append(self.name)

        # meta
        if self.type:
            meta = f'{self.type}'
            if self.subtype: meta += f' ({self.subtype})'
            meta += f', {self.rarity}'
            pt.append(meta)

        # description
        for line in self.description:
            if type(line) is str:
                pt.append(line)
            elif type(line) is List:
                pt.append(line.to_str())
            elif type(line) is Monster:
                pt.append('\n' + line.to_str() + '\n')
            elif type(line) is Table:
                pt.append('\n' + line.to_str() + '\n')

        return '\n'.join(pt)

from .content import *
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
        self.description = kwargs.get('description', None)
        self.figure = kwargs.get('figure', None)
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
            'description': self.description,
            'figure': self.figure,
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

            return figure
        
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
        self.type = m['type']
        self.subtype = m.group('subtype')
        self.rarity = m['rarity']
        self.attunement = m.group('attunement')

        # description
        description = []
        tag = tag.find_next_sibling(['div','p'])
        while tag:
            description.append(tag.get_text(' ', strip=True))
            tag = tag.find_next_sibling(['div','p'])
        self.description = description

        # figure
        figure = process_figure(soup)
        if figure: self.figure = figure

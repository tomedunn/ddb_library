from .content import *
from .figure import Figure
from .list import List
from .monster import Monster
from .table import Table
from bs4 import BeautifulSoup
import re

class Spell(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.level = kwargs.get('level', None)
        self.school = kwargs.get('school', None)
        self.casting_time = kwargs.get('casting_time', None)
        self.range = kwargs.get('range', None)
        self.components = kwargs.get('components', None)
        self.duration = kwargs.get('duration', None)
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
            'content_type': 'Spell',
            'id': self.id,
            'name': self.name,
            'book_path': self.book_path,
            'url': self.url,
            'level': self.level,
            'school': self.school,
            'casting_time': self.casting_time,
            'range': self.range,
            'components': self.components,
            'duration': self.duration,
            'description': [d if type(d) is str else d.to_dict() for d in self.description],
            'figure': self.figure.to_dict() if self.figure else None,
        }

    def __process_html(self):
        """Converts a HTML spell block to a dictionary.
    
        Example:
            spell = construct_spell(spell)
            spell = {
                'name': 'Acid Splash',
                'id': 'acid-splash',
                'casting time': '1 Reaction',
                'components': 'V, S',
                'description': ['An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile .'],
                'duration': '1 Round',
                'level': '1st',
                'range': 'Self',
                'school': 'abjuration',
                'tags': ['Warding']
            }
        """
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
        
        soup = BeautifulSoup(self.html, 'html.parser')
        
        # get spell name and id
        s = soup.find(['h3','h4','h5'])
        a = s.find('a', {'class': 'tooltip-hover spell-tooltip'})
        self.id = a['href'][8:]
        self.name = a.get_text('', strip=False)
        spell = {
            'id': a['href'][8:],
            'name': a.get_text('', strip=False),
            'level': None,
            'school': None,
            'casting time': None,
            'range': None,
            'components': None,
            'duration': None,
            'description': []
        }
        
        # get spell header information
        s = s.find_next_sibling('p')
        RE_SCHOOL = re.compile(r'(abjuration|conjuration|divination|enchantment|evocation|illusion|necromancy|transmutation)', re.IGNORECASE)
        if m := RE_SCHOOL.search(s.get_text('', strip=False)):
            self.school = m.group()
    
        RE_LEVEL = re.compile(r'(cantrip|\d[^\s]+|level \d)', re.IGNORECASE)
        if m := RE_LEVEL.search(s.get_text('', strip=False)):
            self.level = m.group()
    
        RE_HEADER = re.compile(r'^(?P<name>casting time|range|components|duration)\s*:\s*(?P<value>.+)', re.IGNORECASE)
        while True:
            s = s.find_next_sibling('p')
            m = RE_HEADER.match(s.get_text('', strip=False))
            if m:
                spell[m.group('name').lower()] = m.group('value')
            else:
                break
        self.casting_time = spell.get('casting time', self.casting_time)
        self.range = spell.get('range', self.range)
        self.components = spell.get('components', self.components)
        self.duration = spell.get('duration', self.duration)
        
        # get remaining monster stats
        description = []
        s = s.find_previous_sibling()
        for e in s.find_next_siblings(['div','p','ol','ul','table']):
            if e.name == 'p':
                description.append(e.get_text().strip())
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

        return spell

    def to_str(self, rules='2024'):
        """
        Converts the spell to a plain text string.

        Parameters
        ----------
        rules : str
            Determines how the spell is formatted, either ``'2014'`` or ``'2024'``. 
            If ``'2014'`` the stat block will be formatted to match spells published under the 2014 rules (5e), 
            and if ``'2024'`` the format will match those published under the 2024 rules (5.5e).
            Default value ``'2024'``.
        
        Returns
        -------
        text : str
            Plain text spell.
        """
        pt = []
        
        # name
        pt.append(self.name)

        # meta
        if self.level == 'Cantrip':
            pt.append(f'{self.school} {self.level}')
        else:
            pt.append(f'{self.level} {self.school}')

        pt.append(f'Casting Time: {self.casting_time}')
        pt.append(f'Range: {self.range}')
        pt.append(f'Components: {self.components}')
        pt.append(f'Duration: {self.duration}')

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
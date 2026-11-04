from .content import *
from bs4 import BeautifulSoup
import re

class Spell(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.level = kwargs.get('level', None)
        self.casting_time = kwargs.get('casting_time', None)
        self.range = kwargs.get('range', None)
        self.components = kwargs.get('components', None)
        self.duration = kwargs.get('duration', None)
        self.description = kwargs.get('description', None)
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
            'casting_time': self.casting_time,
            'range': self.range,
            'components': self.components,
            'duration': self.duration,
            'description': self.description,
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
        def _parse_list( list ):
            items = [li.get_text(strip=True) for li in list.find_all('li')]
            return dict(type='list', items=items)

        def _parse_monster( mon ):
            #return dmp.construct_monster(mon)
            return '{monster}'
        
        def _parse_table( tab ):
            head = []
            for tr in tab.find('thead').find_all('tr'):
                row = [th.get_text(strip=True) for th in tr.find_all('th')]
                head += [row]

            body = []
            for tr in tab.find('tbody').find_all('tr'):
                row = [td.get_text(strip=True) for td in tr.find_all('td')]
                body += [row]
            return dict(type='table', head=head, body=body)

        soup = BeautifulSoup(self.html, 'html.parser')

        # remove some stuff
        for e in soup.find_all('div', {'class': 'spell-components'}):
            e.unwrap()
        
        for e in soup.find_all('figure'):
            e.decompose()
        
        # get spell name and id
        s = soup.find('h3')
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
        for e in s.find_next_siblings(['div','p','div','ol','ul','table']):
            if e.name == 'p':
                description.append(e.get_text('', strip=False))
            elif e.name == 'div':
                #print(spell['id'])
                description.append(_parse_monster(e))
            elif e.name in ['ol','ul']:
                description.append(_parse_list(e))
            elif e.name == 'table':
                description.append(_parse_table(e))
        
        self.description = description
    
        # post processing
        #spell = post_process_spell(spell)
        
        return spell
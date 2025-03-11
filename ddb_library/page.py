from .magic_item_reference import MagicItemReference
from .monster_reference import MonsterReference
from .myencoder import MyEncoder
from .spell_reference import SpellReference
from .html_processor import process_html
from bs4 import BeautifulSoup
import json
import os
import re

def unwrap_tags(soup):
    for data in soup(['aside','html']):
        data.unwrap()
    
    return soup

def cleanup_div(soup):
    re_reps = re.compile('\n')

    for data in soup(['div']):
        if data.text.strip() == '':
            data.decompose()
    
    for data in soup(['div']):
        if len([c for c in data.contents if c.name]) == 1:
            for c in data.contents:
                if c.name == 'div':
                    data.unwrap()
                    break
    
    for d in soup('div'):
        if len([c for c in d.contents if c.name != None]) == 0:
            d.string = re_reps.sub(' ', d.text.strip())
    
    return soup

def remove_all_tag_attibutes(soup):
    attributes_to_del = [
        'class', 'id', 'style', 'border', 'rowspan', 'colspan', 
        'width', 'height', 'align', 'valign', 'color', 'bgcolor', 
        'cellspacing', 'cellpadding', 'onclick', 'alt', 'title',
        'data-next-link','data-next-title',
        'data-prev-link','data-prev-title',
        'data-content-chunk-id', 'ata-content-chunk-id',
        'data-sheets-value', 
        'data-chapter-slug'
    ]
    
    for attr_del in attributes_to_del: 
        if attr_del in soup.attrs:
            soup.attrs.pop(attr_del)
        [s.attrs.pop(attr_del) for s in soup.find_all() if attr_del in s.attrs]

    return soup

class Page:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        self.name = d.get('name', None)
        self.file = d.get('file', None)
        self.path = d.get('path', None)
        self.type = d.get('type', None)
        self.url = d.get('url', None)
        self.previous_page = d.get('previous_page', '')
        self.next_page = d.get('next_page', '')
        self.modified = d.get('modified', None)

    def __repr__(self):
        return f'{self.__dict__}'

    def copy(self, path, **kwargs):
        """Copies the contents of this file to a new location."""

        dryrun = kwargs.get('dryrun', False)

        if not self.file_exists():
            raise FileNotFoundError("File does not exist.")
        
        # destination folder
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            if dryrun:
                print(f'Directory "{dirname}" not found.')
                print(f'Creating directory "{dirname}".')
            else:
                os.mkdir(dirname)
        
        if dryrun:
            print(f'Copying contents of "{self.path}" to "{path}".')
        else:
            html_text = self.get_html(**kwargs)
            with open(path, 'w') as fout:
                fout.write(html_text)

        return self
    
    def file_exists( self ):
        """Returns True if the file associated with this page exists.
        """
        if self.path:
            return os.path.isfile(self.path)
        else:
            return False
    
    def get_html(self, **kwargs):
        with open(self.path, 'r') as fin:
            html_text = fin.read()

        return process_html(html_text, **kwargs)
    
    def get_magic_items(self, **kwargs):
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin, 'html.parser')

        # remove some annoying formatting stuff
        for d in soup.find_all('div', {'class': 'flexible-double-column'}):
            d.decompose()
        
        magic_items = []
        for h in soup.find_all(['h2','h3','h4']):
            items = []
            a = h.find('a', {'class': 'tooltip-hover magic-item-tooltip'})
            if a:
                items.append(a)
            else:
                p = h.find_next_sibling()
                if not p: continue
                if p.name not in ['p']: continue

                em = p.find('em')
                if not em: continue

                for a in em.find_all('a', {'class': 'tooltip-hover magic-item-tooltip'}):
                    items.append(a)
            
            if not items:
                continue

            # extract all lines between this <h3> and the next one
            s = BeautifulSoup(str(h), 'html.parser')
            for n in h.find_next_siblings():
                if n.name in ['h1','h2','h3']:
                    break
                elif len(n.get_text('', strip=True)) > 0:
                    s.append('\n')
                    s.append(n)
            
            for a in items:
                magic_items += [MagicItemReference({
                    'id': a['href'][13:],
                    'name': h.get_text('', strip=True),
                    'modified': self.modified,
                    'path': self.path,
                    'html': str(s),
                })]

        return magic_items
    
    def get_meta_data( self ):
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin.read(), 'html.parser')

        meta_data = {}
        for m in soup.find_all('meta'):
            k = m.get('property', None)
            v = m.get('content', None)
            if k:
                meta_data[k] = v

        div = soup.find('div', {'id': 'comp-next-nav'})
        if div:
            meta_data['previous_page'] = div['data-prev-link']
            meta_data['next_page'] = div['data-next-link']

        return meta_data
    
    def get_monsters( self ):
        def _monster_class( class_ ):
            re_monster = re.compile(
                r'^(?:'
                    r'Basic-Text-Frame(-\d)?'
                    r'|monster--stat-block'
                    r'|stat-block'
                r')$'
            )
            return class_ and re_monster.match(class_)
        
        def _heading_class( class_ ):
            re_monster = re.compile(
                r'\b(?:'
                    r'heading-anchor'
                    r'|compendium-hr'
                r')\b'
            )
            return class_ and re_monster.match(class_)
        
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin.read(), 'html.parser')

        monsters = []
        for d in soup.find_all('div', class_=_monster_class):
            p = d.find(['h3','p'], {'class': 'Stat-Block-Styles_Stat-Block-Title'})
            if not p: 
                #p = d.find(['h2','h3','h4','h5'], {'class': 'heading-anchor'})
                p = d.find(['h2','h3','h4','h5'], class_=_heading_class)

            if not p: continue

            a = p.find('a', {'class': 'tooltip-hover monster-tooltip'})
            if not a: continue

            monsters.append(MonsterReference({
                'id': a['href'][10:],
                'name': a.get_text('', strip=True),
                'modified': self.modified,
                'path': self.path,
                'html': str(d),
            }))

        return monsters

    def get_name( self ):
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin.read(), 'html.parser')
        meta = soup.find('meta', {'property': 'og:title'})
        if meta:
            return meta['content']
        else:
            return None

    def get_spells( self ):
        #if not self.has_spells():
        #    return []
        
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin, 'html.parser')

        # remove some annoying formatting stuff
        for d in soup.find_all('div', {'class': 'flexible-double-column'}):
            d.decompose()
        
        spells = []
        for h in soup.find_all('h3'):
            a = h.find('a', {'class': 'tooltip-hover spell-tooltip'})
            if not a: continue

            # extract all lines between this <h3> and the next one
            s = BeautifulSoup(str(h), 'html.parser')
            for n in h.find_next_siblings():
                if n.name in ['h1','h2','h3']:
                    break
                elif len(n.get_text('', strip=True)) > 0:
                    s.append('\n')
                    s.append(n)
            
            spells += [SpellReference({
                'id': a['href'][8:],
                'name': a.get_text('', strip=True),
                'modified': self.modified,
                'path': self.path,
                'html': str(s),
            })]

        return spells
    
    def get_tables(self, **kwargs):
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin, 'html.parser')

        # remove some annoying formatting stuff
        for d in soup.find_all('div', {'class': 'flexible-double-column'}):
            d.decompose()
        
        tables = []
        for h in soup.find_all('table', {'class': 'table-compendium'}):
            items = []
            a = h.find('a', {'class': 'tooltip-hover magic-item-tooltip'})
            if a:
                items.append(a)
            else:
                p = h.find_next_sibling()
                if not p: continue
                if p.name not in ['p']: continue

                em = p.find('em')
                if not em: continue

                for a in em.find_all('a', {'class': 'tooltip-hover magic-item-tooltip'}):
                    items.append(a)
            
            if not items:
                continue

            # extract all lines between this <h3> and the next one
            s = BeautifulSoup(str(h), 'html.parser')
            for n in h.find_next_siblings():
                if n.name in ['h1','h2','h3']:
                    break
                elif len(n.get_text('', strip=True)) > 0:
                    s.append('\n')
                    s.append(n)
            
            """for a in items:
                tables += [TableReference({
                    'id': a['href'][13:],
                    'name': h.get_text('', strip=True),
                    'modified': self.modified,
                    'path': self.path,
                    'html': str(s),
                })]"""

        return tables
    
    def has_spells( self ):
        with open(self.path, 'r') as fin:
            soup = BeautifulSoup(fin, 'html.parser')

        for h in soup.find_all('h3'):
            a = h.find('a', {'class': 'tooltip-hover spell-tooltip'})
            if a: 
                return True
        return False
    
    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
    
    def update( self ):
        meta_data = self.get_meta_data()
        self.type = meta_data.get('og:type', self.type)
        self.type = 'toc' if self.type == 'article' else self.type
        self.name = meta_data.get('og:title', self.name)
        self.url = meta_data.get('og:url', self.url)
        self.previous_page = meta_data.get('previous_page', self.previous_page)
        self.next_page = meta_data.get('next_page', self.next_page)
        self.modified = os.path.getmtime(self.path)
        
    def update_available( self ):
        """Returns True if the file for this page has been modified 
        since this was created or last updated.
        """
        if not self.file_exists(): return False
        if not self.modified: return True
        if self.modified < os.path.getmtime(self.path):
            return True
        return False
    
    def validate(self):
        return self.file_exists()
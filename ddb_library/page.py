from .content_reference import ContentReference
from .myencoder import MyEncoder
from .html_processor import process_html
from bs4 import BeautifulSoup
import json
import os
import re

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
        logging = kwargs.get('logging', False)

        if not self.file_exists():
            raise FileNotFoundError("file does not exist")
        
        # destination folder
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            if logging: print(f'Creating directory "{path}".')
            if dryrun:
                print(f'os.mkdir({dirname})')
            else:
                os.mkdir(dirname)
        
        if logging: print(f'Copying contents of "{self.path}" to "{path}".')
        if dryrun:
            print(f'cp "{self.path}" "{path}"')
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
    
    def get_content(self, **kwargs):
        html_options = kwargs.get('html_options', {})
        soup = BeautifulSoup(self.get_html(**html_options), 'html.parser')

        # remove some annoying formatting stuff
        for d in soup.find_all('div', {'class': 'flexible-double-column'}):
            d.decompose()
        
        """tags = [
            ('h2'),
            ('h3'),
            ('h4'),
            ('h5'),
            ('p', 'Stat-Block-Styles_Stat-Block-Title'),
        ]"""
        content_types = kwargs.get('types', ['magic item','monster','spell'])
        content = []
        for h in soup.find_all(['h2','h3','h4','h5','p']):
            if h.name == 'p':
                if 'Stat-Block-Styles_Stat-Block-Title' not in h.get('class', ''):
                    continue
            
            items = []
            a = h.find('a', {'class': ['magic-item-tooltip','monster-tooltip','spell-tooltip']})
            if a:
                items.append(a)
            else:
                p = h.find_next_sibling()
                if not p: continue
                if p.name not in ['p']: continue
                if p.contents[0].name not in ['em']: continue

                # could also check that the parent of each <a> is an <em> ...
                # found one error: 17023-stirge, http://www.dndbeyond.com/sources/dnd/tftyp/a2/the-forge-of-fury

                for a in p.find_all('a', {'class': ['magic-item-tooltip','monster-tooltip']}):
                    items.append(a)
            
            if not items: continue

            # extract all lines between this heading and the next one.
            s = BeautifulSoup(str(h), 'html.parser')
            for n in h.find_next_siblings():
                if n.name in ['h1','h2','h3','h4','h5']:
                    break
                elif len(n.get_text('', strip=True)) > 0:
                    s.append('\n')
                    s.append(n)
            
            # construct references
            for a in items:
                if 'magic-item-tooltip' in a['class']:
                    content_type = 'magic item'
                elif 'monster-tooltip' in a['class']:
                    content_type = 'monster'
                elif 'spell-tooltip' in a['class']:
                    content_type = 'spell'
                else:
                    content_type = None
                
                content_id = a['href'].split('/')[-1]
                m = re.match(r'^(?P<id_num>\d+)-.*$', content_id)
                if not m: continue
                
                if content_type in content_types:
                    content += [ContentReference({
                        'id': content_id,
                        'type': content_type,
                        'name': h.get_text('', strip=True),
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(s),
                    })]
        
        return content

    def get_magic_items(self, **kwargs):
        return self.get_content(types=['magic item'], **kwargs)
    
    def get_meta_data( self ):
        soup = BeautifulSoup(self.get_html(), 'html.parser')

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
    
    def get_monsters( self, **kwargs ):
        return self.get_content(types=['monster'], **kwargs)

    def get_spells(self, **kwargs):
        return self.get_content(types=['spell'], **kwargs)
    
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
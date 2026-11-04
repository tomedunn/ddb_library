from .content_functions import flatten_content
from .html_processor import process_html
from .myencoder import MyEncoder
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
        self.modified = d.get('modified', 0)

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

    def get_header_map(self, **kwargs):
        html_options = {
            'remove_tags': ['figure','footer','header','img','link','meta','script','style'],
            'replace_invisibles': True,
            'unwrap_tags': [('div', {'class': 'flexible-double-column'})],
        }
        html_options = kwargs.get('html_options', html_options)
        
        soup = BeautifulSoup(self.get_html(**html_options), 'html.parser')

        headers = kwargs.get('headers', ['h1','h2','h3','h4','h5'])
        path = re.match(r'.*/([\w-]+/[\w-]+)', self.url)[1]

        headings = [{
            'type': 'h0',
            'children': [],
        }]

        soup = soup.find('div', {'class': ['p-article','p-article-content','article-main']})
        if not soup:
            # this should throw an error I think ...
            return headings[0]['children']

        
        for h in soup.contents:
            if h.name not in headers: continue
            if 'visually-hidden' in h['class']: continue

            a = h.find('a', {'class': ['magic-item-tooltip','monster-tooltip','spell-tooltip']})
            if a: continue # don't include content headers

            id = h.get('id', None)
            label = h.get_text('', strip=True)
            if id:
                heading = {
                    'type': h.name,
                    'id': f'{path}#{id}',
                    'name': label,
                    'children': [],
                }
                while headers.index(h.name)+1 < len(headings):
                    headings.pop()
                
                headings[-1]['children'].append(heading)
                headings.append(heading)

        return headings[0]['children']
    
    def get_html(self, **kwargs):
        with open(self.path, 'r') as fin:
            html_text = fin.read()

        return process_html(html_text, **kwargs)

    def get_content(self, **kwargs):
        """
        Extracts content from the page.
    
        Parameters
        ----------
        content_types : (n) str
            A list of content types to include in the final output. Allowed content types include `'Encounter'`,
            `'Figure'`, `'Item'`, `'Magic Item'`, `'Monster'`, `'Spell'`, `'Table'`, `'Treasure'`, and `'Vehicle'`.
            Default value ``['Encounter','Figure','Item','Magic Item','Monster','Spell','Table','Treasure','Vehicle']``.
        
        format : str
            The format to return the results in. Either `'dict'` for nested dictionaries based on headers, 
            or `'list'` for a list of contents.
            Default value `'list'`.
        
        html_options : dict
            Pre-processing options to be passed on to ``self.get_html()``.
            Default value
            ```python
            {
                'remove_empty_tags': [
                    'div',
                ],
                'remove_tags': [
                    'footer','header','link','meta','script','style','br',
                    ('div', {'class': ['Flowchart-Block']}),
                    ('p', {'class': ['compendium-image-subtitle']}),
                ],
                'replace_invisibles': True,
                'replace_dashes': True,
                'unwrap_tags': [
                    'blockquote',
                    ('div', {'class': None}),
                    ('div', {'class': ['flexible-double-column']}),
                    ('div', {'class': ['efota-title','efota-title-text']}),
                    ('div', {'class': ['table-overflow-wrapper']}),
                    ('div', {'class': ['red-statblock-text']}),
                    (['ol','ul']),
                ],
            }
            ```
        
        Returns
        -------
        content : dict
            Content formatted in a header map format
        """
        content_types = kwargs.get('content_types', ['Encounter','Figure','Item','Magic Item','Monster','Spell','Table','Treasure','Vehicle'])

        html_options = {
            'remove_empty_tags': [
                'div',
            ],
            'remove_tags': [
                'footer','header','link','meta','script','style','br',
                ('div', {'class': ['Flowchart-Block']}),
                ('p', {'class': ['compendium-image-subtitle']}),
            ],
            'replace_invisibles': True,
            'replace_dashes': True,
            'unwrap_tags': [
                'blockquote',
                ('div', {'class': None}),
                ('div', {'class': ['flexible-double-column']}),
                ('div', {'class': ['efota-title','efota-title-text']}),
                ('div', {'class': ['table-overflow-wrapper']}),
                ('div', {'class': ['red-statblock-text']}),
                (['ol','ul']),
            ],
        }
        soup = BeautifulSoup(self.get_html(**kwargs.get('html_options', html_options)), 'html.parser')

        headers = ['h1','h2','h3','h4','h5','h6']
        path = re.match(r'.*/([\w-]+/[\w-]+)', self.url)[1]

        headings = [{
            'type': 'h0',
            'children': [],
            'contents': [],
        }]
        heading = headings[0]

        # find main body
        soup = soup.find('div', {'class': ['p-article','p-article-content','article-main']})
        if not soup:
            # this should throw an error I think ...
            return headings[0]['children']

        def extract_monsters(tag):
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
            monsters = []
            number = 1
            monster = ''
            for c in tag.contents:
                """
                Dungeon of the Mad Mage has some content marked like this ... sigh ...
                <span class="Serif-Character-Style_Bold-Serif plural-monster-tooltip">
                    <a class="tooltip-hover monster-tooltip">
                        thugs
                    </a>
                </span>
                """
                if c.name == 'a':
                    if 'monster-tooltip' not in c.get('class', []): continue
                    monster = c['href'].split('/')[-1]
                    m = re.match(r'^(?P<id_num>\d+)-.*$', monster)
                    if not m: continue
                    monsters += [(number, monster)]
                    number = 1
                elif not c.name:
                    m = re.match(r'.*\b(?P<number>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|\.)\b', c.get_text('', strip=False), re.IGNORECASE)
                    if not m: continue
                    number = m['number'].lower()
                    if re.match(r'\d+', number):
                        number = int(number)
                    else:
                        number = TEXT_TO_NUMBER.get(number, 1)
                elif c.name == 'span':
                    if 'plural-monster-tooltip' in c.get('class', ''):
                        if not c.a: continue
                        if 'monster-tooltip' not in c.a.get('class', []): continue
                        monster = c.a['href'].split('/')[-1]
                        m = re.match(r'^(?P<id_num>\d+)-.*$', monster)
                        if not m: continue
                        monsters += [(number, monster)]
                        number = 1

                else:
                    pass

            return monsters
        
        def extract_treasure(tag):
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
            
            treasures = []
            number = 1
            for c in tag.contents:
                if c.name == 'a':
                    if 'magic-item-tooltip' in c.get('class', []): 
                        id = c['href'].split('/')[-1]
                        if not re.match(r'^(?P<id_num>\d+)-.*$', id): continue
                        treasures += [(number, f'magic-items/{id}')]
                        number = 1
                    elif 'item-tooltip' in c.get('class', []): 
                        id = c['href'].split('/')[-1]
                        if not re.match(r'^(?P<id_num>\d+)-.*$', id): continue
                        treasures += [(number, f'equipment/{id}')]
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
                            treasures += [(number, m['money'])]
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

            return treasures

        def tag_type(tag):
            if tag.name == None:
                return None
            elif tag.name in ['table']:
                return 'table'
            elif tag.name in ['figure']:
                return 'figure'
            elif tag.name in ['ol','ul']:
                return 'list'
            elif tag.name in ['h1','h2','h3','h4','h5']:
                if 'visually-hidden' in tag.get('class', []):
                    return None
                elif tag.find('a', {'class': ['item-tooltip']}):
                    return 'item'
                elif tag.find('a', {'class': ['magic-item-tooltip']}):
                    return 'magic item'
                elif tag.find('a', {'class': ['monster-tooltip']}):
                    return 'variant monster'
                elif tag.find('a', {'class': ['spell-tooltip']}):
                    return 'spell'
                else:
                    return 'structural header'
            elif tag.name == 'div':
                if 'Basic-Text-Frame' in tag.get('class', []):
                    p = tag.find(['p','h1','h2','h3','h4','h5'])
                    if p.find('a', {'class': ['monster-tooltip']}):
                        return 'monster'
                    elif p.find('a', {'class': ['vehicles-tooltip']}):
                        return 'vehicle'
                    else:
                        # mostly odd monster stat block
                        return 'unknown'
                elif 'stat-block' in tag.get('class', []):
                    p = tag.find(['p','h1','h2','h3','h4','h5'])
                    if p.find('a', {'class': ['monster-tooltip']}):
                        return 'monster'
                    else:
                        # these are either spell stat blocks, class/subclass monsters, 
                        # or stat blocks that don't directly link to their monster page
                        return 'monster'
            elif tag.name in ['p','li']:
                if tag.get_text('', strip=False).startswith('Treasure.'):
                    return 'treasure'
                elif extract_monsters(tag):
                    return 'encounter'
                elif extract_treasure(tag):
                    return 'treasure'
            
            return None

        # find all headers
        tag = soup.contents[0]
        while tag:
            tt = tag_type(tag)

            if tt == 'structural header':
                id = tag.get('id', None)
                url = f'{self.url}#{id}'
                tag.find('a', {'class': ['spell-tooltip']})
                label = tag.get_text('', strip=True)
                heading = {
                    'type': tag.name,
                    'id': f'{path}#{id}',
                    'name': label,
                    'url': url,
                    'children': [],
                    'contents': [],
                }
                while headers.index(tag.name)+1 < len(headings):
                    headings.pop()
                
                headings[-1]['children'].append(heading)
                headings.append(heading)
                tag = tag.next_sibling

            elif tt == 'item':
                s = BeautifulSoup(str(tag), 'html.parser')
                for n in tag.find_next_siblings():
                    tn = tag_type(n)
                    if tn in ['item','magic item','monster','spell'] and headers.index(n.name) <= headers.index(tag.name):
                        break
                    elif tn in ['structural header'] and headers.index(n.name) <= headers.index(tag.name):
                        break
                    else:
                        s.append('\n')
                        s.append(n)
                else:
                    n = None

                tag = n

                if 'Item' in content_types:
                    heading['contents'].append({
                        'content_type': 'Item',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(s),
                    })
                
            elif tt == 'magic item':
                s = BeautifulSoup(str(tag), 'html.parser')
                for n in tag.find_next_siblings():
                    tn = tag_type(n)
                    if tn in ['magic item','item'] and headers.index(n.name) <= headers.index(tag.name):
                        break
                    elif tn in ['structural header'] and headers.index(n.name) <= headers.index(tag.name):
                        break
                    else:
                        s.append('\n')
                        s.append(n)
                else:
                    n = None

                tag = n

                if 'Magic Item' in content_types:
                    heading['contents'].append({
                        'content_type': 'Magic Item',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(s),
                    })

            elif tt == 'monster':
                if 'Monster' in content_types:
                    heading['contents'].append({
                        'content_type': 'Monster',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(tag),
                    })
                tag = tag.next_sibling

            elif tt == 'spell':
                s = BeautifulSoup(str(tag), 'html.parser')
                for n in tag.find_next_siblings():
                    tn = tag_type(n)
                    if tn in ['structural header','spell']:
                        break
                    else:
                        s.append('\n')
                        s.append(n)
                else:
                    n = None

                tag = n

                if 'Spell' in content_types:
                    heading['contents'].append({
                        'content_type': 'Spell',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(s),
                    })

            elif tt == 'vehicle':
                if 'Vehicle' in content_types:
                    heading['contents'].append({
                        'content_type': 'Vehicle',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(tag),
                    })
                tag = tag.next_sibling

            elif tt == 'table':
                if 'Table' in content_types:
                    heading['contents'].append({
                        'content_type': 'Table',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(tag),
                    })
                tag = tag.next_sibling

            elif tt == 'list':
                print(tag)
                tag = tag.next_sibling

            elif tt == 'encounter':
                if 'Encounter' in content_types:
                    heading['contents'].append({
                        'content_type': 'Encounter',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(tag),
                    })

                tag = tag.next_sibling
            
            elif tt == 'treasure':
                s = BeautifulSoup(str(tag), 'html.parser')
                for n in tag.find_next_siblings():
                    tn = tag_type(n)
                    if tn in ['structural header','magic item','spell','vehicle']:
                        break
                    else:
                        s.append('\n')
                        s.append(n)
                else:
                    n = None
                
                tag = n

                if 'Treasure' in content_types:
                    heading['contents'].append({
                        'content_type': 'Treasure',
                        'modified': self.modified,
                        'path': self.path,
                        'html': str(s),
                    })

            elif tt == 'figure':
                heading['contents'].append({
                    'content_type': 'Figure',
                    'modified': self.modified,
                    'path': self.path,
                    'html': str(tag),
                })
                tag = tag.next_sibling

            elif tt == 'unknown':
                tag = tag.next_sibling
            
            else:
                tag = tag.next_sibling

        format = kwargs.get('format', 'list')
        if format == 'dict':
            return headings[0]['children']
        elif format == 'list':
            return flatten_content(headings[0]['children'])
        else:
            raise Exception(f'"{format}" is not a valid format option.')
    
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
            meta_data['previous_page'] = div.get('data-prev-link', '')
            meta_data['next_page'] = div.get('data-next-link', '')

        link = soup.find('link', {'rel': 'canonical'})
        if link: meta_data['url'] = link['href']
        
        return meta_data
    
    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
    
    def update( self ):
        meta_data = self.get_meta_data()
        self.type = meta_data.get('og:type', self.type)
        self.name = meta_data.get('og:title', self.name)
        self.url = meta_data.get('og:url', self.url)
        self.url = meta_data.get('url', self.url)
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
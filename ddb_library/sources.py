from .myencoder import MyEncoder
from bs4 import BeautifulSoup
from .html_processor import process_html
import json
import os
import re

def create_book_acronym(name):
    """Returns and acronym from the given book title.
    """
    m = re.search(r'(?P<title>[^\(]+)(?P<year>\(\d+\))?$', name, re.IGNORECASE)
    
    acronym = ''.join([token[0:1] for token in m.group('title').split(' ')])
    year = '' if not m.group('year') else ' ' + m.group('year')

    return acronym + year

class Sources:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        self.name = d.get('name', 'sources')
        self.file = d.get('file', 'sources.html')
        self.path = d.get('path', './sources.html')
        self.url = d.get('url', 'https://www.dndbeyond.com/sources')
        self.modified = d.get('modified', None)
        if not self.modified: self.update()

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
        if not self.file_exists():
            raise FileNotFoundError("File does not exist.")
        
        with open(self.path, 'r') as fin:
            html_text = fin.read()

        return process_html(html_text, **kwargs)
    
    def load_books(self):
        """loads books from a local sources.html file downloaded from DDB.
        """
        RE_URL = re.compile(
            r'(?P<url>'
                r'(?P<root_url>https://[^#]+\.com)?'
                r'(?P<url_path>[^#]+)'
            r')'
            r'(?P<tag>#.+)?'
            , re.IGNORECASE)

        if not self.file_exists(): return
        soup = BeautifulSoup(self.get_html(), 'html.parser')

        books = []
        for a in soup.find_all('a', class_='sources-listing--item'):
            # get book url and convert to a local path
            url = 'https://www.dndbeyond.com/' + a['href']
            url_path = f'{os.path.dirname(self.path)}' + RE_URL.match(url).group('url_path')
            path = re.sub(r'compendium\/(rules|adventures)|sources\/dnd', 'sources', str(url_path))

            # determine if the book is owned and then remove that data
            # to make extracting the book name easier
            matches = a.findAll('span', class_='owned-content')
            owned_content = True if matches else False
            if matches:
                for match in a.findAll('span', class_='owned-content'):
                    match.decompose()
            
            # get the book name
            name = a.get_text('', strip=True)
            acronym = create_book_acronym(name)

            # construct the book
            books.append(dict(
                name=name, 
                acronym=acronym, 
                url=url, 
                path=path, 
                owned_content=owned_content
            ))
        
        return books

    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
    
    def update( self ):
        if not self.file_exists():
            raise FileNotFoundError("File does not exist.")
        
        self.modified = os.path.getmtime(self.path)
        return self
        
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
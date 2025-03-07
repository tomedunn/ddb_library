from .book import Book
from .sources import Sources
from .myencoder import MyEncoder
from bs4 import BeautifulSoup
import json
import re
import os

def create_book_acronym(name):
    """Returns and acronym from the given book title.
    """
    m = re.search(r'(?P<title>[^\(]+)(?P<year>\(\d+\))?$', name, re.IGNORECASE)
    
    acronym = ''.join([token[0:1] for token in m.group('title').split(' ')])
    year = '' if not m.group('year') else ' ' + m.group('year')

    return acronym + year

class Library:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        self.name = d.get('name', None)
        self.path = d.get('path', None)
        if 'sources' in d:
            self.add_sources(d['sources'])
        else:
            self.add_sources({
                'file': d.get('sources_file', 'sources.html'),
                'path': os.path.join(self.path, d.get('sources_file', 'sources.html')),
            })
        self.books = []
        self.add_books(d.get('books', []))

    def __repr__(self):
        return f'{self.__dict__}'
    
    def add_book(self, *args, **kwargs):
        book = args[0] if args else kwargs
        replace = kwargs.get('replace', False)
        
        if type(book) is dict:
            book = Book(**book, root_path=self.path)
        elif type(book) is not Book:
            print('unable to process book')
        
        if not self.book(name=book.name):
            self.books.append(book)
        elif replace:
            for i in range(len(self.books)):
                if book.name == self.books[i].name:
                    self.books[i] = book

        return self
    
    def add_books(self, books, **kwargs):
        for book in books:
            self.add_book(book, **kwargs)
        return self
    
    def add_sources(self, *args, **kwargs):
        sources = args[0] if args else kwargs
        
        if type(sources) is dict:
            sources = Sources(**sources, root_path=self.path)
        elif type(sources) is not Sources:
            print('unable to process book')
        
        self.sources = sources

        return self
    
    def book(self, *args, **kwargs):
        name = args[0] if args else kwargs.get('name', None)
        acronym = kwargs.get('acronym', None)
        for book in self.books:
            if name and book.name == name:
                return book
            elif acronym and book.acronym == acronym:
                return book
        return None
    
    def copy(self, path, **kwargs):
        """Copies the contents of this library to a new location."""

        dryrun = kwargs.get('dryrun', False)

        # destination folder
        if not os.path.isdir(path):
            if dryrun:
                print(f'Directory "{path}" not found.')
                print(f'Creating directory "{path}".')
            else:
                os.mkdir(path)
        
        # sources file
        if self.sources:
            sources_path = os.path.join(path, self.sources.file)
            self.sources.copy(sources_path, **kwargs)
        
        # sources folder
        sources_path = os.path.join(path, 'sources')
        if not os.path.isdir(sources_path):
            if dryrun:
                print(f'Directory "{sources_path}" not found.')
                print(f'Creating directory "{sources_path}".')
            else:
                os.mkdir(sources_path)

        for book in self.books:
            if not book.validate(): continue
            book_path = os.path.join(path, 'sources', os.path.basename(book.path))
            book.copy(book_path, **kwargs)

        return self

    def load_books(self, **kwargs):
        """Loads each book in library.
        """
        logging = kwargs.get('logging', False)
        skip_books = kwargs.get('skip_books', [])

        if logging: print('Loading books.')
        for book in self.books: 
            if not book.is_owned_content(): continue
            if book.name in skip_books: continue
            
            try:
                if logging: print(f' - Loading pages for "{book.name}"', end=' ... ')
                book.load_folder()
                if logging: print('success.')
            except FileNotFoundError as e:
                if logging: print(e)

            """if book.validate():
                if logging: print('success.')
            else:
                if logging: print('ERROR!')
                for page in book.pages:
                    if not page.validate():
                        if logging: print(f'   * Unable to find file for "{page.url}".')"""
        
        if logging: print('Books loaded.')
        return self

    def load_book_pages(self, **kwargs):
        for book in self.books:
            if not book.is_owned_content(): continue
            if book.name in kwargs.get('skip_books', []): continue
            book.load_pages()

    def load_sources(self, **kwargs):
        """loads books from a local sources.html file downloaded from DDB.
        """
        RE_URL = re.compile(
            r'(?P<url>'
                r'(?P<root_url>https://[^#]+\.com)?'
                r'(?P<url_path>[^#]+)'
            r')'
            r'(?P<tag>#.+)?'
            , re.IGNORECASE)
        
        logging = kwargs.get('logging', True)

        if logging: print('Loading sources', end=' ... ')

        if not self.sources.file_exists(): return
        soup = BeautifulSoup(self.sources.get_html(), 'html.parser')

        for a in soup.find_all('a', class_='sources-listing--item'):
            # get book url and convert to a local path
            url = 'https://www.dndbeyond.com/' + a['href']
            url_path = f'{self.path}' + RE_URL.match(url).group('url_path')
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
            self.add_book(dict(
                name=name, 
                acronym=acronym, 
                url=url, 
                path=path,
                owned_content=owned_content
            ), **kwargs)
        
        if logging: print(f'success.')
        if logging: print(f'Found {self.size()} books.')
        return self

    def get_book_names(self):
        return [book.name for book in self.books]
    
    def get_magic_items(self, **kwargs):
        magic_items = []
        if kwargs.get('acronyms', None):
            for acronym in kwargs['acronyms']:
                book = self.book(acronym=acronym)
                if not book: continue
                if not book.is_owned_content(): continue
                if book.name in kwargs.get('skip_books', []): continue
                magic_items += book.get_magic_items()
        else:
            for name in kwargs.get('names', self.get_book_names()):
                book = self.book(name)
                if not book.is_owned_content(): continue
                if book.name in kwargs.get('skip_books', []): continue
                magic_items += book.get_magic_items()

        # merge magic_items found in multiple books
        magic_item_dict = {}
        for magic_item in magic_items:
            if magic_item.id in magic_item_dict:
                magic_item_dict[magic_item.id].sources += magic_item.sources
                magic_item_dict[magic_item.id].modified = magic_item.modified
                magic_item_dict[magic_item.id].path = magic_item.path
                magic_item_dict[magic_item.id].html = magic_item.html
                
            else:
                magic_item_dict[magic_item.id] = magic_item

        magic_items = [v for v in magic_item_dict.values()]
        
        return magic_items
    
    def get_monsters(self, **kwargs):
        monsters = []
        if kwargs.get('acronyms', None):
            for acronym in kwargs['acronyms']:
                book = self.book(acronym=acronym)
                if not book: continue
                if not book.is_owned_content(): continue
                if book.name in kwargs.get('skip_books', []): continue
                monsters += book.get_monsters()
        else:
            for name in kwargs.get('names', self.get_book_names()):
                book = self.book(name)
                if not book.is_owned_content(): continue
                if book.name in kwargs.get('skip_books', []): continue
                monsters += book.get_monsters()

        # merge monsters found in multiple books
        monster_dict = {}
        for monster in monsters:
            if monster.id in monster_dict:
                monster_dict[monster.id].sources += monster.sources
                monster_dict[monster.id].modified = monster.modified
                monster_dict[monster.id].path = monster.path
                monster_dict[monster.id].html = monster.html
                
            else:
                monster_dict[monster.id] = monster

        monsters = [v for v in monster_dict.values()]
        
        return monsters
    
    def get_spells(self, **kwargs):
        spells = []
        if kwargs.get('acronyms', None):
            for acronym in kwargs['acronyms']:
                book = self.book(acronym=acronym)
                if not book: continue
                if not book.is_owned_content(): continue
                if book.name in kwargs.get('skip_books', []): continue
                spells += book.get_spells()
        else:
            for name in kwargs.get('names', self.get_book_names()):
                book = self.book(name)
                if not book.is_owned_content(): continue
                if book.name in kwargs.get('skip_books', []): continue
                spells += book.get_spells()

        # merge spells found in multiple books
        spell_dict = {}
        for spell in spells:
            if spell.id in spell_dict:
                spell_dict[spell.id].sources += spell.sources
                spell_dict[spell.id].modified = spell.modified
                spell_dict[spell.id].path = spell.path
                spell_dict[spell.id].html = spell.html
            else:
                spell_dict[spell.id] = spell

        spells = [v for v in spell_dict.values()]
        
        return spells

    def size(self):
        """Returns the number of books in the library.
        """
        return len(self.books)

    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
    
    def update(self):
        if self.sources.update_available():
            self.load_sources(replace=False)
        
        for book in self.books:
            if book.update_available():
                book.update()
        
        return self
    
    def update_available(self):
        """Returns True if the source file or if any of the books in this 
        library have been modified since this was created or last updated.
        """
        if self.sources.update_available():
            return True
        
        for book in self.books:
            if book.update_available():
                return True
        
        return False

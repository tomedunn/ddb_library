from .content_functions import flatten_content
from .book import Book
from .myencoder import MyEncoder
from .sources import Sources
import json
import os

class Library:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        if not d: return

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

    @classmethod
    def from_json_file(cls, json_path):
        with open(json_path, 'r') as fin:
            json_dict = json.load(fin)
        return cls(json_dict)

    def __repr__(self):
        return f'{self.__dict__}'
    
    def add_book(self, *args, **kwargs):
        """
        Adds a book to this library.

        Parameters
        ----------
        
        path : str
            A path to the folder containing the book's files. Must be provided with a keyword.
        
        replace : bool
            If ``True`` then the given book will replace an existing book with the same path if it
            already exists in the library. If ``False`` then the existing book will not be replaced.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Library`` for chaining commands.
        """
        book = args[0] if args else kwargs
        replace = kwargs.get('replace', False)

        if type(book) is str:
            book = Book(path=book)
        elif type(book) is dict:
            book = Book(**book, root_path=self.path)
        elif type(book) is not Book:
            print('unable to process book')
        
        if not self.book(path=book.path):
            self.books.append(book)
        elif replace:
            for i in range(len(self.books)):
                if book.path == self.books[i].path:
                    self.books[i] = book

        return self
    
    def add_books(self, books, **kwargs):
        """
        Adds a list of books to this library.

        Parameters
        ----------
        
        books : list
            Books to be added to the library. Each book can be a ``Book``, a ``dict`` with items that can be used to
            construct a ``Book``, or the path to a folder containing a book as a ``str``.
        
        replace : bool
            If ``True`` then the given book will replace an existing book with the same path if it
            already exists in the library. If ``False`` then the existing book will not be replaced.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Library`` for chaining commands.
        """
        for book in books:
            self.add_book(book, **kwargs)
        return self
    
    def add_sources(self, *args, **kwargs):
        """
        Adds a sources file to this library.

        Parameters
        ----------

        file : str
            The name of the sources file.
        
        path : str
            The path to the folder containing the sources file.
        
        Returns
        -------

        self : Library
            A reference to this ``Library`` for chaining commands.
        """
        sources = args[0] if args else kwargs
        
        if type(sources) is dict:
            sources = Sources(**sources, root_path=self.path)
        elif type(sources) is not Sources:
            print('unable to process book')
        
        self.sources = sources

        return self
    
    def book(self, *args, **kwargs):
        """
        Returns the first book that matches the given title, acronym, or path.

        The default argument is ``name``, which can be provided without providing a keyword.
        The other arguments, ``acronym`` and ``path``, require a keyword. If multiple keyword
        arguments are provided then the first book to match any of them is returned.

        Parameters
        ----------

        name : str
            The title of the book.
        
        acronym : str
            The acronym of the book.
        
        path : str
            The path to the folder containing the book.
        
        Returns
        -------

        book : Book
            The first book that matches the given criteria. If no book matches, returns ``None``.
        """
        name = args[0] if args else kwargs.get('name', None)
        acronym = kwargs.get('acronym', None)
        path = kwargs.get('path', None)
        for book in self.books:
            if name and book.name == name:
                return book
            elif acronym and book.acronym == acronym:
                return book
            elif path and book.path == path:
                return book
        return None
    
    def copy(self, path, **kwargs):
        """
        Copies the contents of this library to a new location.

        Parameters
        ----------

        path : str
            Location for the copied file.

        dryrun : bool
            If ``False`` the file will be copied. If ``True`` the file won't be copied and the commands for copying will be printed instead.
            Default value ``False``.

        logging : bool
            If ``True`` a log will be printed.
            Default value ``False``.

        kwargs : dict
            Optional arguments passed to each book's `copy` function.
        
        Returns
        -------

        self : Library
            A self reference for chaining functions together.
        """
        
        dryrun = kwargs.get('dryrun', False)
        logging = kwargs.get('logging', True)

        if logging: print(f'Copying library contents to "{path}".')

        # destination folder
        if not os.path.isdir(path):
            if logging: print(f'Creating directory "{path}".')
            if dryrun:
                print(f'os.mkdir({path})')
            else:
                os.mkdir(path)
        
        # sources file
        if self.sources and kwargs.get('sources', True):
            sources_path = os.path.join(path, self.sources.file)
            self.sources.copy(sources_path, **kwargs)
        
        # sources folder
        sources_path = os.path.join(path, 'sources')
        if not os.path.isdir(sources_path):
            if logging: print(f'Creating directory "{sources_path}".')
            if dryrun:
                print(f'os.mkdir({sources_path})')
            else:
                os.mkdir(sources_path)

        if logging: print(f'Copying books.')
        for book in self.books:
            if not book.validate(): continue
            if not book.name in kwargs.get('book_names', self.get_book_names()): continue
            book_path = os.path.join(path, 'sources', os.path.basename(book.path))
            if logging: print(f' - Copying book "{book.name}".')
            book.copy(book_path, **kwargs)

        return self

    def load_books(self, **kwargs):
        """
        Attempts to load each book in the library.

        Loading a book means searching for its folder in the library's sources folder, and then scanning
        the files in that folder to determine the book's table of contents (if it exist), pages, and page order.

        Parameters
        ----------

        logging : bool
            If ``True`` then details about the function's progress will be printed to ``sys.stdout``.
            Default value ``False``.
        
        skip_books : list
            Titles of books to skip during the process.
        
        Returns
        -------

        self : Library
            A reference to this ``Library`` for chaining commands.
        """
        logging = kwargs.get('logging', True)
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
                if logging: print(f'{e}.')
        
        if logging: print('Books loaded.')
        return self

    def load_sources(self, **kwargs):
        """
        Loads books found in this library's sources file.

        The library's ``sources`` file is scanned for books. New books are added to this library
        and existing books are updated.

        Parameters
        ----------

        logging : bool
            If ``True`` then details about the function's progress will be printed to ``sys.stdout``.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Library`` for chaining commands.
        """
        
        logging = kwargs.get('logging', True)

        if logging: print('Loading sources', end=' ... ')

        books = self.sources.load_books()
        for book in books:
            tbook = self.book(path=book['path'])
            if tbook:
                tbook.update(**book)
            else:
                self.add_book(book, **kwargs)
                """tbook = self.book(path=book['path'])
                try:
                    tbook.load_folder()
                except FileNotFoundError as e:
                    pass"""
        
        self.sources.update()
        if logging: print(f'success.')
        if logging: print(f'Found {self.size()} books in sources.')
        if logging: print(f'Found {len([book.name for book in self.books if book.owned_content])} owned books.')
        return self

    def get_book_names(self, **kwargs):
        """
        Returns a list of names for books in this library.
        
        Returns
        -------

        book_names : list
            The names of the books in this library.
        """
        if 'update_available' in kwargs:
            return [book.name for book in self.books if book.update_available() == kwargs['update_available']]
        elif 'validate' in kwargs:
            return [book.name for book in self.books if book.validate() == kwargs['validate']]
        else:
            return [book.name for book in self.books]
    
    def get_content(self, **kwargs):
        """
        Extracts content from each book in this library.
    
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
                    ('div', {'class': re.compile(r'flexible-double-column.*')}),
                    ('div', {'class': ['efota-title','efota-title-text']}),
                    ('div', {'class': ['table-overflow-wrapper']}),
                    ('div', {'class': ['red-statblock-text']}),
                    ('div', {'class': ['hangingIndent']}),
                    ('div', {'class': ['spells-chapter','_idGenObjectLayout-2']}), # 2014 control weather spell
                    ('div', {'class': ['spell-components']}), # 2024 PH spells
                    ('div', {'class': ['condensed-group']}), # some magic item property lists
                    (lambda tag: tag.name == 'div' and 'ui-droppable' in tag.get('class', []) and 'stats' not in tag.get('class', []) and 'stat-block-ability-scores' not in tag.get('class', [])),
                ],
            }
            ```
        
        Returns
        -------
        content : list
            Content from the library.
        """
        format = kwargs.pop('format', 'list')
        logging = kwargs.get('logging', False)
        content_types = kwargs.get('content_types', ['Encounter','Figure','Item','Magic Item','Monster','Spell','Table','Treasure','Vehicle'])
        if logging: print('Extracting ' + ', '.join(content_types) + ' content from library.')
        lib_content = []
        if kwargs.get('acronyms', None):
            for acronym in kwargs['acronyms']:
                book = self.book(acronym=acronym)
                if not book: continue
                if not book.is_owned_content(): continue
                if not book.validate(): continue
                if book.name in kwargs.get('skip_books', []): continue
                if logging: print(f' - "{book.name}" ...', end='')
                content = book.get_content(**kwargs, format='dict')
                if logging: print(f' done')
                lib_content.append(content)
        else:
            for name in kwargs.get('names', self.get_book_names()):
                book = self.book(name)
                if not book.is_owned_content(): continue
                if not book.validate(): continue
                if book.name in kwargs.get('skip_books', []): continue
                if logging: print(f' - "{book.name}" ...', end='')
                content = book.get_content(**kwargs, format='dict')
                if logging: print(f' done')
                lib_content.append(content)

        if format == 'dict':
            return lib_content
        elif format == 'list':
            return flatten_content(lib_content)
        else:
            raise Exception(f'"{format}" is not a valid format option.')

    def save_json(self, **kwargs):
        path = kwargs.get('path', self.path)
        file = kwargs.get('file', 'library.json')
        file_path = os.path.join(path, file)
        print(f'Saving library to {file_path}.')
        with open(file_path, 'w') as fout:
            json.dump(json.loads(self.to_json()), fout, indent=4)

    def size(self):
        """Returns the number of books in the library.
        """
        return len(self.books)

    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
    
    def update(self, **kwargs):
        """
        Updates the sources and books in this library.

        Checks if this library's sources or books have been modified and updates the details of any that have.

        Parameters
        ----------

        logging : bool
            If ``True`` then details about the function's progress will be printed to ``sys.stdout``.
            Default value ``False``.

        Returns
        -------

        self : Library
            A reference to this ``Library`` for chaining commands.
        """
        logging = kwargs.get('logging', False)

        if self.sources.update_available():
            if logging: print(f'Updating sources.')
            self.load_sources(replace=False)
        
        for book in self.books:
            if book.update_available():
                if logging: print(f'Updating book "{book.name}".')
                book.update()
        
        return self
    
    def update_available(self):
        """
        Returns ``True`` if the library's files have been modified since they were last scanned.

        Returns
        -------

        ans : bool
            ``True`` if the library's sources or any of its books have been modified.
            Returns ``False`` otherwise.
        """
        if self.sources.update_available():
            return True
        
        for book in self.books:
            if book.update_available():
                return True
        
        return False

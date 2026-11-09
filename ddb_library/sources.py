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
        """
        Copies the contents of this file to a new location.

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
            Optional arguments passed to ``self.get_html``.
        
        Returns
        -------

        self : Page
            A self reference for chaining functions together.
        """

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
        """
        Returns ``True`` if the file associated with this page exists.
        
        Returns
        -------
        ans : bool
            ``True`` if the page's file exists, ``False`` otherwise.
        """
        if self.path:
            return os.path.isfile(self.path)
        else:
            return False
    
    def get_html(self, **kwargs):
        """
        Returns the page's HTML.

        Parameters
        ----------

        extract_main_body : bool
            If ``True`` a new simplified version of the page is constructed using just the main body 
            and a few useful elements from outside of it.
            Default value ``False``.
    
        remove_tags : list
            A list of tags to be removed. Tags may be given as either a string, in which case all tags with that name 
            are removed, or as a tuple containing the tag name and a dict of attributes and values that the tag must have
            in order to be removed.
            Default value ``[]``.
        
        unwrap_tags : list
            A list of tags to be unwrapped. Tags may be given as either a string, in which case all tags with that name 
            are unwrapped, or as a tuple containing the tag name and a dict of attributes and values that the tag must have
            in order to be removed.
            Default value ``[]``.
        
        remove_tag_attributes : list
            Removes the given attributes from all tags that have one.
            Default value ``[]``.
        
        cleanup_divs : bool
            If ``True`` then removes all div tags with no text inside them, unwraps all div tags that contain only a single
            div tag inside of them, and if a div tag contains only text then all the text is merged onto a single line.
            Default value ``False``.
    
        remove_empty_tags : list
            A list of tags to be removed if they contain no text inside of them. Tags may be given as either a string, in 
            which case all tags with that name are unwrapped, or as a tuple containing the tag name and a dict of attributes 
            and values that the tag must have in order to be removed.
            Default value ``[]``.
        
        remove_comments : bool
            If ``True`` then all comments are removed from the text.
            Default value ``False``.
    
        remove_blank_lines : bool
            If ``True`` then all lines of length zero are removed.
            Default value ``False``.
        
        replace_invisibles : bool
            If ``True`` then several non-standard white-space characters are replaced with a standard space character,
            and zero width characters are removed.
            Default value ``False``.
        
        replace_dashes : bool
            If ``True`` then several dash-like characters are replaced with standard dash characters ``-``.
            Default value ``False``.
    
        prettify : bool
            Applies several cosmetic changes to make the html text easier to read.
            Default value ``False``.
        
        Returns
        -------

        html : str
            The page's HTML text.
        """
        if not self.file_exists():
            raise FileNotFoundError("File does not exist.")
        
        with open(self.path, 'r') as fin:
            html_text = fin.read()

        return process_html(html_text, **kwargs)
    
    def load_books(self):
        """
        Scans sources for books.

        Each book found is returned as a ``dict`` with the following information:
        ```python
        dict(
            name=name, 
            acronym=acronym, 
            url=url, 
            path=path, 
            owned_content=owned_content
        )
        ```
        
        Returns
        -------

        books : list
            The books found during the scan. Each book takes the form of a ``dict``.
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

        # new library format
        div = soup.find('div', {'id': 'S:0'})
        if div:
            for c in div.find_all('div', {'class': re.compile(r'SourceCard_nameGroup_.*')}):
                a = c.a
                p = c.p

                # get book url and convert to a local path
                if not a['href']: continue
                url = 'https://www.dndbeyond.com' + a['href']
                url_path = f'{os.path.dirname(self.path)}' + RE_URL.match(url).group('url_path')
                path = re.sub(r'compendium\/(rules|adventures)|sources\/dnd', 'sources', str(url_path))

                # determine if the book is owned
                status = p.get_text('', strip=True)
                owned_content = status in ['Purchased','Free','Shared with me']

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
        
        # old library format
        for a in soup.find_all('a', class_='sources-listing--item'):
            # get book url and convert to a local path
            if not a['href']: continue
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
        """
        Updates this page.

        Scans this page's file for details and updates them if they've changed. 

        Returns
        -------

        self : Page
            A reference to this ``Page`` for chaining commands.
        """
        if not self.file_exists():
            raise FileNotFoundError("File does not exist.")
        
        self.modified = os.path.getmtime(self.path)
        return self
        
    def update_available( self ):
        """
        Returns ``True`` if this page's file has been modified since it was last scanned.

        Returns
        -------

        ans : bool
            ``True`` if this page's file has been modified.
            Returns ``False`` otherwise.
        """
        if not self.file_exists(): return False
        if not self.modified: return True
        if self.modified < os.path.getmtime(self.path):
            return True
        return False
    
    def validate(self):
        return self.file_exists()
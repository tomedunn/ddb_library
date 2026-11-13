from .content_functions import flatten_content
from .page import Page
from bs4 import BeautifulSoup
import os
import re

class Book:
    def __init__(self, *args, **kwargs):
        d = args[0] if args else kwargs
        self.name = d.get('name', None)
        self.acronym = d.get('acronym', None)
        self.url = d.get('url', None)
        self.owned_content = d.get('owned_content', None)
        #self.path = d.get('path', '.') + f'/{self.acronym}'
        if 'path' in d:
            self.path = d.get('path', None)
        else:
            self.path = d.get('root_path', '.') + f'/{self.acronym}'
        self.table_of_contents = None
        self.add_toc(d.get('table_of_contents', None))

        self.pages = []
        self.add_pages(d.get('pages', []))
        #self.pages = [Page(**page) for page in d.get('pages', [])]

    def __repr__(self):
        return f'{self.__dict__}'

    def add_page(self, page, **kwargs):
        """
        Adds a page to this book.

        Parameters
        ----------
        
        page : Page
            A page to add to the book.
        
        replace : bool
            If ``True`` then the given page will replace an existing page with the same path.
            If ``False`` then the page will only be added if the book doesn't have any pages with the same path already.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Book`` for chaining commands.
        """
        replace = kwargs.get('replace', False)

        if type(page) is Page:
            new_page = page
        else:
            new_page = Page(**page, root_path=self.path)

        if not self.page(path=new_page.path):
            self.pages.append(new_page)
        elif replace:
            for i in range(self.size()):
                if self.pages[i].path == new_page.path:
                    self.pages[i] = new_page
        
        return self
    
    def add_pages(self, pages, **kwargs):
        """
        Adds a list of pages to this book.

        Parameters
        ----------
        
        pages : (n) Page
            A list of pages to add to the book.
        
        replace : bool
            If ``True`` then each page will replace an existing page with the same path.
            If ``False`` then a page will only be added if the book doesn't have any pages with the same path already.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Book`` for chaining commands.
        """
        for page in pages:
            self.add_page(page, **kwargs)
        return self
    
    def add_toc(self, page, **kwargs):
        """
        Adds a table of contents page to this book.

        Parameters
        ----------
        
        page : Page
            The table of contents page.
        
        replace : bool
            If ``True`` then the given page will replace the book's existing table of contents page. 
            If ``False`` then the page will only be added if no table of contents exists already.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Book`` for chaining commands.
        """
        if not page: return self

        replace = kwargs.get('replace', False)

        if type(page) is Page:
            new_page = page
        else:
            new_page = Page(**page, root_path=self.path)
        
        if not self.table_of_contents or replace:
            self.table_of_contents = new_page
        
        return self
    
    def copy(self, path, **kwargs):
        """
        Copies the contents of this book to a new location.

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
            Optional arguments passed to each page's `copy` function.
        
        Returns
        -------

        self : Book
            A self reference for chaining functions together.
        """

        dryrun = kwargs.get('dryrun', False)
        logging = kwargs.get('logging', True)

        if not self.folder_exists():
            raise FileNotFoundError("Folder does not exist.")
        
        # destination folder
        if not os.path.isdir(path):
            if logging: print(f'Creating directory "{path}".')
            if dryrun:
                print(f'os.mkdir({path})')
            else:
                os.mkdir(path)
        
        # table of contents
        if self.table_of_contents:
            toc_path = os.path.join(path, self.table_of_contents.file)
            self.table_of_contents.copy(toc_path, **kwargs)
        
        # book pages
        for page in self.pages:
            page_path = os.path.join(path, page.file)
            page.copy(page_path, **kwargs)

        return self
    
    def folder_exists(self):
        """
        Returns ``True`` if the folder associated with this book exists.
        
        Returns
        -------
        ans : bool
            ``True`` if the book's folder exists, ``False`` otherwise.
        """
        return os.path.isdir(self.path)

    def get_html(self, **kwargs):
        if kwargs.get('extract_main_body', False):
            html_start = [kwargs.pop('html_start', 
                '\n'.join(['<!DOCTYPE html>','<html lang="en-us">','<meta charset="utf-8"/>']),
            )]
            html_end = [kwargs.pop('html_end', '</html>')]
        else:
            html_start = []
            html_end = []
        
        book_html = []
        if self.table_of_contents:
            book_html.append(self.table_of_contents.get_html(**kwargs, html_start='', html_end=''))
        
        for page in self.pages:
            book_html.append(page.get_html(**kwargs, html_start='', html_end=''))
        
        return '\n'.join(html_start + book_html + html_end)
    
    def get_content(self, **kwargs):
        """
        Extracts content from each page in the book.
    
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
            Content formatted in a list format
        """
        format = kwargs.pop('format', 'list')

        book_content = {
            'type': 'h0',
            'id': re.match(r'.*/([\w-]+)$', self.url)[1],
            'name': self.name,
            'url': self.url,
            'children': [],
            'contents': [],
        }
        for page in self.pages:
            book_content['children'].extend(page.get_content(**kwargs, format='dict'))

        if format == 'dict':
            return book_content
        elif format == 'list':
            return flatten_content(book_content)
        else:
            raise Exception(f'"{format}" is not a valid format option.')

    def get_header_map(self, **kwargs):
        headings_map = {
            'type': 'h0',
            'id': re.match(r'.*/([\w-]+)$', self.url)[1],
            'name': self.name,
            'children': [],
        }
        for page in self.pages:
            headings_map['children'].extend(page.get_header_map(**kwargs))
        
        return headings_map
    
    def is_owned_content(self):
        """
        Checks if the book is owned content.
        
        Returns
        -------

        ans : bool
            Returns ``True`` if the book is owned and ``False`` if its not.
        """
        return self.owned_content

    def last_modified(self):
        """
        Determines when the book was last modified.
        
        Returns
        -------

        mtime : float
            Returns the most recent modified time of any of the books pages. If the book has no pages then
            ``0`` is returned.
        """
        mtime = 0 if not self.table_of_contents else self.table_of_contents.modified
        if self.pages:
            mtime = max(mtime, max([p.modified for p in self.pages]))
        return mtime

    def load_folder(self, **kwargs):
        """
        Searches the book's folder for pages and adds them to the book.
        
        Any file in the book's folder with a ``.html`` suffix is scanned and added to the book.
        If the scan reveals a URL for the page that matches the book's URL then that page is treated as 
        a table of contents page.

        Parameters
        ----------

        replace : bool
            If ``True`` then pages will replace existing pages with the same path.
            If ``False`` then pages will only be added if the book doesn't have a page with the same path already.
            Default value ``False``.
        
        Returns
        -------

        self : Library
            A reference to this ``Book`` for chaining commands.
        """
        if not self.folder_exists():
            raise FileNotFoundError("folder doesn't exist")
        
        # add a page for each html file in folder
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            for file in filenames:
                if file.endswith('.html'):
                    file = os.path.join(dirpath, file).replace(self.path+'/', '')
                    file_path = os.path.join(self.path, file)
                    page = Page(file=file, path=file_path)
                    page.update()
                    if page.url == self.url:
                        self.add_toc(page, **kwargs)
                    else:
                        self.add_page(page, **kwargs)
        
        # construct final set of pages with toc at the front and in correct page order
        if self.table_of_contents:
            self.load_toc()
        
        self.order_pages()
        
        return self

    def load_toc(self, **kwargs):
        """
        Extracts book and page details from the table of contents.

        If a page is found that isn't already present in the book's page list then that page is added.
        
        Returns
        -------

        self : Library
            A reference to this ``Book`` for chaining commands.
        """
        RE_URL = re.compile(
            r'(?P<url>'
                r'(?P<root_url>https?://[^#]+\.com)?'
                r'(?P<url_path>/'
                    r'(?P<sources_url>(?:(?:adventures|compendium|dnd|rules|sources)/)+)'
                    r'(?P<book_acronym>[^\./#]+)/'
                    r'(?P<page_url>[^\.#]+)'
                r')'
            r')'
            r'(?P<tag>#.+)?'
            , re.IGNORECASE)
        
        if not self.table_of_contents: return []

        with open(self.table_of_contents.path, 'r') as fin:
            soup = BeautifulSoup(fin.read(), 'html.parser')

        if not soup: return []
        
        urls = []
        tags = soup.find_all('blockquote', {'class': 'compendium-toc-blockquote'})
        tags += soup.find_all('div', {'class': 'compendium-toc-full'})
        for d in tags:
            for a in d.find_all('a'):
                m = RE_URL.match(a['href'])
                if not m: continue
                if m.group('page_url') == 'credits-mobile': continue
                url = '/' + m.group('book_acronym') + '/' + m.group('page_url')
                url = url[:-1] if url.endswith('/') else url # fix for one link in strixhaven

                # fix 2014 books
                url = re.sub(r'(?<=/)(mm|dmg|phb|basic-rules)/', '\\1-2014/', url)
                url = url.lower()

                if url not in urls:
                    urls.append(url)
        
        # add all other files that match urls in the table of contents
        book_pages = []
        for url in urls:
            matched_page = None
            for i in range(self.size()):
                if not self.pages[i].url: continue
                if self.pages[i].url.endswith(url):
                    matched_page = self.pages.pop(i)
                    break
            
            if matched_page:
                book_pages.append(matched_page)
            else:
                book_pages.append(Page(url=url))
        self.pages = book_pages
        return self

    def order_pages(self, **kwargs):
        """
        Arranges the book's pages in the order they appear in the digital book.
        
        Returns
        -------

        self : Library
            A reference to this ``Book`` for chaining commands.
        """
        debugging = kwargs.get('debugging', False)
        pages = []
        for i in range(self.size()):
            if self.pages[i].previous_page == '':
                pages.append(self.pages.pop(i))
                break

        while self.size() > 0:
            for i in range(self.size()):
                if debugging: print(self.pages[i].name, self.pages[i].previous_page, self.pages[i].next_page)
                if self.pages[i].previous_page in pages[-1].url:
                    pages.append(self.pages.pop(i))
                    break
                elif i == self.size()-1:
                    self.pages = pages + self.pages
                    return self
        
        self.pages = pages
        return self

    def page(self, *args, **kwargs):
        """
        Returns the first page that matches the given name, file, path, or url.

        The default argument is ``name``, which can be provided without providing a keyword.
        The other arguments, ``file``, ``path`` and ``url`` require a keyword. If multiple keyword
        arguments are provided then the first page to match any of them is returned.

        Parameters
        ----------

        name : str
            The title of the page.
        
        file : str
            The acronym of the page.
        
        path : str
            The path to the page's file.
        
        url : str
            The url of the page.
        
        Returns
        -------

        page : Page
            The first page that matches the given criteria. If no page matches, returns ``None``.
        """
        name = args[0] if args else kwargs.get('name', None)
        file = kwargs.get('file', None)
        path = kwargs.get('path', None)
        url  = kwargs.get('url', None)
        for page in self.pages:
            if name and page.name == name:
                return page
            elif file and page.file == file:
                return page
            elif path and page.path == path:
                return page
            elif url  and page.url  == url:
                return page
        return None
    
    def size(self):
        """Returns the number of pages in the book.
        """
        return len(self.pages)
    
    def update(self, **kwargs):
        """
        Updates the pages in this book.

        Checks if this book's pages have been modified and updates the details of any that have.

        Returns
        -------

        self : Book
            A reference to this ``Book`` for chaining commands.
        """
        self.name = kwargs.get('name', self.name)
        self.acronym = kwargs.get('acronym', self.acronym)
        self.url = kwargs.get('url', self.url)
        self.owned_content = kwargs.get('owned_content', self.owned_content)
        self.path = kwargs.get('path', self.path)
        
        if self.table_of_contents and self.table_of_contents.update_available():
            self.table_of_contents.update()
            self.load_toc()

        if self.pages:
            self.order_pages()
            for page in self.pages:
                if page.update_available():
                    page.update()
        elif self.folder_exists():
            if len(os.listdir(self.path)) > 0:
                self.load_folder()
        
        return self

    def update_available(self, **kwargs):
        """
        Returns ``True`` if any of the book's files have been modified since they were last scanned.

        Returns
        -------

        ans : bool
            ``True`` if any of the book's files have been modified.
            Returns ``False`` otherwise.
        """
        logging = kwargs.get('logging', False)

        if self.table_of_contents and self.table_of_contents.update_available():
            if logging: print('Update available - table of contents')
            return True
        
        if self.pages:
            for page in self.pages:
                if page.update_available():
                    if logging: print('Update available - pages')
                    return True
        
        elif self.folder_exists():
            if len(os.listdir(self.path)) > 0:
                if logging: print('Update available - folder')
                return True
        
        if logging: print('Update not available')
        return False

    def validate(self):
        if not self.path:
            return False
        
        if not os.path.isdir(self.path):
            return False
        
        if self.table_of_contents and not self.table_of_contents.validate():
            return False
        
        for page in self.pages:
            if not page.validate():
                return False
            
        return True
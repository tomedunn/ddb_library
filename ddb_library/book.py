from .myencoder import MyEncoder
from .page import Page
from bs4 import BeautifulSoup
import json
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
        replace = kwargs.get('replace', False)

        if type(page) is Page:
            new_page = page
        else:
            new_page = Page(**page, root_path=self.path)
        
        """for i in range(self.size()):
            if self.pages[i].path == new_page.path and replace:
                self.pages[i] = new_page
                return self
        
        self.pages.append(new_page)"""

        if not self.page(path=new_page.path):
            self.pages.append(new_page)
        elif replace:
            for i in range(self.size()):
                if self.pages[i].path == new_page.path:
                    self.pages[i] = new_page
        
        return self
    
    def add_pages(self, pages, **kwargs):
        for page in pages:
            self.add_page(page, **kwargs)
        return self
    
    def add_toc(self, page, **kwargs):
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
        """Copies the contents of this folder to a new location."""

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
        book_content = []
        for page in self.pages:
            page_content = page.get_content(**kwargs)
            for content in page_content:
                content.sources = [{
                    "name": self.name,
                    "acronym": self.acronym,
                    "url": self.url,
                    "path": self.path,
                    "page": {
                        "name": page.name,
                        "url": page.url,
                        "path": page.path,
                    }
                }]
            
            book_content += page_content
        return book_content
    
    def get_magic_items(self, **kwargs):
        return self.get_content(types=['magic item'], **kwargs)
    
    def get_monsters(self, **kwargs):
        return self.get_content(types=['monster'], **kwargs)
    
    def get_spells(self, **kwargs):
        return self.get_content(types=['spell'], **kwargs)
    
    def is_owned_content(self):
        return self.owned_content

    def last_modified(self):
        lm = 0 if not self.table_of_contents else self.table_of_contents.modified
        return max(lm, max([p.modified for p in self.pages]))

    def load_folder(self, **kwargs):
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
                    if page.type == 'toc':
                        self.add_toc(page)
                    else:
                        self.add_page(page)
        
        # construct final set of pages with toc at the front and in correct page order
        if self.table_of_contents:
            self.load_toc()
        
        self.order_pages()
        
        return self

    def load_toc(self, **kwargs):
        """Finds all pages listed in the book's table of contents.
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
    
    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, cls=MyEncoder, **kwargs)
    
    def update(self, **kwargs):
        self.name = kwargs.get('name', self.name)
        self.acronym = kwargs.get('acronym', self.acronym)
        self.url = kwargs.get('url', self.url)
        self.owned_content = kwargs.get('owned_content', self.owned_content)
        self.path = kwargs.get('path', self.path)
        
        if self.table_of_contents and self.table_of_contents.update_available():
            self.load_toc()

        if self.pages:
            for page in self.pages:
                if page.update_available():
                    page.update()
        elif self.folder_exists():
            if len(os.listdir(self.path)) > 0:
                self.load_folder()
        
        return self

    def update_available(self):
        """Returns True if any of the page files for this book have been 
        modified since this was created or last updated.
        """
        if self.table_of_contents and self.table_of_contents.update_available():
            return True
        
        if self.pages:
            for page in self.pages:
                if page.update_available():
                    return True
        elif self.folder_exists():
            if len(os.listdir(self.path)) > 0:
                return True
        
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
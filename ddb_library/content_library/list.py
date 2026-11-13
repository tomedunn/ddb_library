from .content import *
from bs4 import BeautifulSoup

class List(Content):
    def __init__(self, **kwargs):
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.list_type = kwargs.get('list_type', None)
        self.list_items = kwargs.get('list_items', [])
        self.html = kwargs.get('html', None)
        if self.html: self.__process_html__()

    def __process_html__(self):
        """
        Extracts parameters from html.
        """
        soup = BeautifulSoup(self.html, 'html.parser')

        tag = soup.contents[0]
        self.list_type = 'ordered' if tag.name == 'ol' else 'unordered'

        self.list_items = [li.get_text().strip() for li in tag.find_all('li')]
    
    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'List',
            'book_path': self.book_path,
            'url': self.url,
            'list_type': self.list_type,
            'list_items': self.list_items,
        }

    def to_str(self):
        """
        Converts the list to a plain text string.
        
        Returns
        -------
        text : str
            Plain text list.
        """
        pt = []

        i = 0
        for li in self.list_items:
            i += 1
            prefix = f' {i}.' if self.list_type == 'ordered' else ' *'
            pt.append(f'{prefix} {li}')

        return '\n'.join(pt)

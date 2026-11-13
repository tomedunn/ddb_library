from .content import *
from .figure import Figure
from .list import List
from .table import Table
from bs4 import BeautifulSoup

class Item(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.description = kwargs.get('description', [])
        for line in self.description:
            if type(line) is dict:
                if line['content_type'] == 'List':
                    line = List(**line)
                elif line['content_type'] == 'Table':
                    line = Table(**line)
        self.figure = kwargs.get('figure', None)
        if type(self.figure) is dict: self.figure = Figure(**self.figure)
        self.html = kwargs.get('html', None)
        if self.html: self.__process_html()

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Item',
            'id': self.id,
            'name': self.name,
            'book_path': self.book_path,
            'url': self.url,
            'description': [d if type(d) is str else d.to_dict() for d in self.description],
            'figure': self.figure.to_dict() if self.figure else None,
        }

    def __process_html(self):
        def process_figure(soup):
            figure = {}
            t = soup.find('span', class_='artist-credit')
            if t: figure['artist'] = t.get_text()
        
            t = soup.find('img')
            if t: figure['src'] = t['src']
        
            t = soup.find('figcaption')
            if t: figure['caption'] = t.get_text()

            if figure:
                return Figure(
                    book_path=self.book_path,
                    url=self.url,
                    **figure,
                )
            else:
                return None
        
        soup = BeautifulSoup(self.html, 'html.parser')
        
        # get spell name and idd
        tag = soup.find(['h1','h2','h3','h4','h5'])
        a = tag.find('a', {'class': 'item-tooltip'})
        self.id = a['href'][11:]
        self.name = tag.get_text().strip()

        # get remaining monster stats
        description = []
        s = tag.next_sibling
        for tag in s.find_next_siblings(['p','li','ol','ul','table']):
            if tag.name in ['p']:
                description.append(tag.get_text().strip())
            elif tag.name == 'li':
                print(str(tag))
            elif tag.name in ['ol','ul']:
                description.append(List(**{
                    'content_type': 'List',
                    'book_path': self.book_path,
                    'url': self.url,
                    'html': str(tag),
                }))
            elif tag.name == 'table':
                description.append(Table(**{
                    'content_type': 'Table',
                    'book_path': self.book_path,
                    'url': self.url,
                    'html': str(tag),
                }))
        
        self.description = description

        # figure
        self.figure = process_figure(soup)

    def to_str(self, rules='2024'):
        """
        Converts the magic item to a plain text string.

        Parameters
        ----------
        rules : str
            Determines how the magic item is formatted, either ``'2014'`` or ``'2024'``. 
            If ``'2014'`` the stat block will be formatted to match magic items published under the 2014 rules (5e), 
            and if ``'2024'`` the format will match those published under the 2024 rules (5.5e).
            Default value ``'2024'``.
        
        Returns
        -------
        text : str
            Plain text magic item.
        """
        pt = []
        
        # name
        pt.append(self.name)

        # description
        for line in self.description:
            if type(line) is str:
                pt.append(line)
            elif type(line) is List:
                pt.append(line.to_str())
            elif type(line) is Table:
                pt.append('\n' + line.to_str() + '\n')

        return '\n'.join(pt)
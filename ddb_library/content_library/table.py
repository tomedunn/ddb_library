from .content import *
from bs4 import BeautifulSoup
import re

class Table(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.head = kwargs.get('head', None)
        self.body = kwargs.get('body', None)
        self.body_tags = kwargs.get('body_tags', None)
        self.html = kwargs.get('html', None)
        if self.html: self.__process_html()

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Table',
            'id': self.id,
            'name': self.name,
            'book_path': self.book_path,
            'url': self.url,
            'head': self.head,
            'body': self.body,
            'body_tags': self.body_tags,
        }

    def __process_html(self):
        """Converts a HTML table block to a dictionary.
        """
        soup = BeautifulSoup(self.html, 'html.parser')

        tab = soup.find('caption')
        if tab:
            self.name = tab.get_text(strip=True)
            tab = tab.find(['h1','h2','h3','h4','h5'])
            if tab:
                self.id = tab.get('id', None)


        self.head = []
        thead = soup.find('thead')
        if thead:
            for tr in thead.find_all('tr'):
                row = [th.get_text().strip() for th in tr.find_all('th')]
                self.head += [row]

        self.body = []
        for tr in soup.find('tbody').find_all('tr'):
            row = [td.get_text().strip() for td in tr.find_all(['th','td'])]
            self.body += [row]

        self.body_tags = []
        for tr in soup.find('tbody').find_all('tr'):
            row = [td.name for td in tr.find_all(['th','td'])]
            self.body_tags += [row]

    def to_str(self, rules='2024'):
        """
        Converts the spell to a plain text string.

        Parameters
        ----------
        rules : str
            Determines how the spell is formatted, either ``'2014'`` or ``'2024'``. 
            If ``'2014'`` the stat block will be formatted to match spells published under the 2014 rules (5e), 
            and if ``'2024'`` the format will match those published under the 2024 rules (5.5e).
            Default value ``'2024'``.
        
        Returns
        -------
        text : str
            Plain text spell.
        """
        pt = []
        
        # name
        if self.name: pt.append(self.name)

        if self.head:
            pt.append('| ' + ' | '.join(self.head[0]) + ' |')
            pt.append('|' + '|'.join([':----:' for h in self.head[0]]) + '|')

        for row in self.body:
            pt.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(pt)

from .content import *
from bs4 import BeautifulSoup

class Item(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.description = kwargs.get('description', None)
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
            'description': self.description,
        }

    def __process_html(self):
        """Converts a HTML item to a dictionary.
        """
        def _parse_list( list ):
            items = [li.get_text(strip=True) for li in list.find_all('li')]
            return dict(type='list', items=items)
        
        def _parse_table( tab ):
            head = []
            for tr in tab.find('thead').find_all('tr'):
                row = [th.get_text(strip=True) for th in tr.find_all('th')]
                head += [row]

            body = []
            for tr in tab.find('tbody').find_all('tr'):
                row = [td.get_text(strip=True) for td in tr.find_all('td')]
                body += [row]
            return dict(type='table', head=head, body=body)

        soup = BeautifulSoup(self.html, 'html.parser')
        
        # get spell name and idd
        tag = soup.find(['h1','h2','h3','h4','h5'])
        a = tag.find('a', {'class': 'item-tooltip'})
        self.id = a['href'][11:]
        self.name = tag.get_text('', strip=False)

        # get remaining monster stats
        description = []
        s = tag.next_sibling
        for tag in s.find_next_siblings(['p','ol','ul','table']):
            if tag.name == 'p':
                description.append(tag.get_text('', strip=False))
            elif tag.name in ['ol','ul']:
                description.append(_parse_list(tag))
            elif tag.name == 'table':
                description.append(_parse_table(tag))
        
        self.description = description
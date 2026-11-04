from .content import *
from bs4 import BeautifulSoup

class Figure(Content):
    def __init__(self, **kwargs):
        self.book_path = kwargs.get('book_path', None)
        self.url = kwargs.get('url', None)
        self.artist = kwargs.get('artist', None)
        self.src = kwargs.get('src', None)
        self.caption = kwargs.get('caption', None)
        self.html = kwargs.get('html', None)
        if self.html: self.__process_html()

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Figure',
            'book_path': self.book_path,
            'url': self.url,
            'artist': self.artist,
            'src': self.src,
            'caption': self.caption,
        }

    def __process_html(self):
        """Converts a HTML item to a dictionary.
        """
        soup = BeautifulSoup(self.html.replace('\n',''), 'html.parser')

        tag = soup.find('span', class_='artist-credit')
        if tag: self.artist = tag.get_text()
    
        tag = soup.find('img')
        if tag: self.src = tag['src']
    
        tag = soup.find('figcaption')
        if tag: self.caption = tag.get_text()
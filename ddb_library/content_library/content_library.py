from .encounter import *
from .figure import *
from .item import *
from .magic_item import *
from .monster import *
from .spell import *
from .table import *
from .treasure import *
import json
import re

class ContentLibrary:
    def __init__(self, contents=[], file=None):
        """
        Constructs a new content library.

        Parameters
        ----------
        content : list
            A list of content.
        
        file : str
            If provided then the content will be loaded from file.
        """
        self.contents = []
        if contents:
            self.set_contents(contents)
        else:
            if file:
                self.from_json_file(file)

    def __repr__(self):
        return f'{self.to_dict()}'

    def from_json_file(self, file):
        """
        Loads content from a JSON file.

        Parameters
        ----------
        file : str
            The name of the file.
        """
        with open(file, 'r') as fin:
            self.set_contents(json.load(fin))

    def to_dict(self):
        return dict(contents=[c.copy() if type(c) is dict else c.to_dict() for c in self.contents])

    def to_json_file(self, file, compact_lists=False, **kwargs):
        """
        Saves contents as a JSON file.

        Parameters
        ----------
        file : str
            The name of the file.
        
        compact_lists : bool
            If ``True`` then lists will be written in a compact form with one entry per line.
            Default value ``False``.
        """
        s = json.dumps(self.to_dict(), **kwargs)
        if compact_lists:
            s = re.sub(r'(\[)[\s\n]+([^:,\[\]]+)(?=,|\])', r'\1\2', s)
            s = re.sub(r'(,)[\s\n]+([^:,\[\]]+)(?=,|\])', r'\1 \2', s)
            s = re.sub(r'(,[\s\n]+[^:,\[\]]+?)[\s\n]+(?=\])', r'\1', s)
        
        with open(file, 'w') as fout:
            fout.write(s)

    def get_contents(self, book_paths=[], ids=None, content_types=[]):
        """
        Returns a filtered list of contents.

        Parameters
        ----------
        book_path : str
            A regular expression to be applied to encounter ``book_path`` attribute using the ``re.match`` function.
        
        Returns
        -------
        contents : list
            The contents that matched the given book_path regular expression.
        """
        content_ids = ids if ids else []

        book_paths = book_paths if book_paths else [r'.*']
        content_types = content_types if content_types else [Encounter, Treasure]
        
        for c in self.contents:
            if not any([re.match(book_path, c.book_path) for book_path in book_paths]):
                continue
            if not any([isinstance(c, ct) for ct in content_types]):
                continue
            content_ids.append(c.id)

        return [c for c in self.contents if c.id in content_ids]

    def set_contents(self, contents):
        self.contents = []
        for e in contents:
            if type(e) is dict:
                try:
                    content_type = e.get('content_type', '').lower()
                    if content_type == 'encounter':
                        self.contents.append(Encounter(**e))
                    elif content_type == 'figure':
                        self.contents.append(Figure(**e))
                    elif content_type == 'item':
                        self.contents.append(Item(**e))
                    elif content_type == 'magic item':
                        self.contents.append(MagicItem(**e))
                    elif content_type == 'monster':
                        self.contents.append(Monster(**e))
                    elif content_type == 'spell':
                        self.contents.append(Spell(**e))
                    elif content_type == 'table':
                        self.contents.append(Table(**e))
                    elif content_type == 'treasure':
                        self.contents.append(Treasure(**e))
                    else:
                        # should throw an error
                        #self.contents.append(e)
                        pass
                except:
                    self.contents.append(e)
            else:
                self.contents.append(e)

    def summary(self):
        summary = {
            'Total': len(self.contents),
            'Encounters': len([c for c in self.contents if type(c) is Encounter]),
            'Figures': len([c for c in self.contents if type(c) is Figure]),
            'Items': len([c for c in self.contents if type(c) is Item]),
            'Magic Items': len([c for c in self.contents if type(c) is MagicItem]),
            'Monsters': len([c for c in self.contents if type(c) is Monster]),
            'Spells': len([c for c in self.contents if type(c) is Spell]),
            'Tables': len([c for c in self.contents if type(c) is Table]),
            'Treasures': len([c for c in self.contents if type(c) is Treasure]),
            'unknowns': len([c for c in self.contents if type(c) is dict]),
        }
        return '\n'.join(f'{k}: {v}' for k,v in summary.items())
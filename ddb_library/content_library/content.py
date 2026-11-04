import uuid

class Content:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.book_path = kwargs.get('book_path', None)

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Content',
            'id': self.id,
            'book_path': self.book_path,
        }

    def book(self):
        """
        Returns the first part of the book_path.

        Returns
        ----------
        book : str
            The name of the book the encounter comes from.
        """
        return self.book_path.split('; ')[0]

    def book_path_list(self):
        """
        Returns the book_path in list form.

        Returns
        ----------
        book_path : list
            The book_path in list form.
        """
        return self.book_path.split('; ')[0]
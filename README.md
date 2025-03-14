# ddb_library

This module provides tools for managing and parsing books from D&D Beyond in html form.

## File structure

To make use of this module, you'll need to download html files from D&D Beyond and store them locally on your computer in the following format.

```
library folder
├── sources.html
└── sources
    ├── book1
    │   ├── file1.html
    │   └── file2.html
    ├── book2
    │   ├── file1.html
    │   ├── sub-book1
    │   │   ├── file1.html
    │   │   └── file2.html
    │   └── sub-book2
    │       ├── file1.html
    │       └── file2.html
    └── book3
        ├── file1.html
        └── file2.html
```

Within the library's root folder there should be a `sources.html` files as well as a `sources` folder that contains a subfolder for each book, containing the book's pages saved as html files.

The `sources.html` comes from [https://www.dndbeyond.com/sources](https://www.dndbeyond.com/sources) and the folder for each book is based on the last part of the book's url on D&D Beyond. 

For example, the url for the _D&D Free Rules (2024)_ is [https://www.dndbeyond.com/sources/dnd/free-rules](https://www.dndbeyond.com/sources/dnd/free-rules) and so the folder for it is `./sources/free-rules`.

The file `sources.html` can have a different name, but that name will need to be specified when creating the library.

In rare cases, a book will also need sub-folders to hold component books or individual adventures. The names of these sub-folders must also follow the urls for those pages. For example, the url for the adventure "The Sunless Citadel" from _[Tales from the Yawning Portal](https://www.dndbeyond.com/sources/dnd/tftyp)_ is [https://www.dndbeyond.com/sources/dnd/tftyp/a1/the-sunless-citadel](https://www.dndbeyond.com/sources/dnd/tftyp/a1/the-sunless-citadel). In this case, the folder for the book would be `./sources/tftyp` and the sub-folder for the adventure would be `./sources/tftyp/a1`.

## Creating a new library

A new library can be created in the following way, where `path='./example` designates the location of the library `sources` folder and sources file `sources_file='Sources - D&D Beyond.html'`.

```python
import ddb_library as dbl

lib = dbl.Library(
    name='local DDB library',
    path='./example',
    sources_file='Sources - D&D Beyond.html',
)
```
If `sources_file` is not provided then the library will use a default value of `sources.html`.

An initial list of books can be added by loading the given sources file.

```python
lib.load_sources()
```

The library's list of books can then be finalized by loading each book.

```python
lib.load_books()
```

These steps can take a minute or two for libraries with a large number of books stored in them.

Finally, the constructed library can be stored as a `.json` file in the library's directory. The default name of the file is `library.json`.

```python
lib.save_json()
```

This allows the library to be loaded more quickly in the future as follows.

```python
lib = dbl.Library().from_json_file('./example/library.json')
```

## Updating an existing library
If the html files in an existing library are updated, or if new books are added, the library can be updated as follows.

```python
lib = dbl.Library().from_json_file('./example/library.json')
lib.update()
```

This will check each file to see if it has been modified since the last time recorded in `library.json`. If any of the files in a book have been updated then the whole book is reconstructed. Remember to save the library after updating.

## Copying an existing library

An existing library can be copied to a new location as shown in the following example.

```python
import ddb_library as dbl

library_path = './example_copy/library.json'
lib = dbl.Library().from_json_file(library_path)

lib.copy('./example_copy')
```

This will copy the file structure and all of the html files in the library to the `./example_copy` directory.

Once the files are copied, a new library will need to be constructed.
```python
clib = dbl.Library(
    name='local DDB library',
    path='./example_copy',
    sources_file='Sources - D&D Beyond.html',
)
clib.load_sources()
clib.load_books()
clib.save_json()
```

By default, the library's html files are copied exactly, but a number of options can be added to fine tune what content is copied over and what is removed from the copied file.

```python
options = {
    'extract_main_body': True,
    'remove_blank_lines': True,
    'remove_comments': True,
    'remove_empty_tags': ['p','section'],
    'remove_tags': ['footer','header','link','script','style'],
}
lib.copy('./example_copy', **options)
```

The library can also be copied to its own directory. This is only practically useful when combined with formatting options, like the ones in the above example. As a point of caution, it's best to avoid this until you know what formatting options work best for you.

## Extracting book contents

This module contains functions for locating and extracting different kinds of content from an existing library, individual books, or pages. Currently three kinds of content are supported: magic items, monsters, and spells.

```python
import ddb_library as dbl

library_path = './example_copy/library.json'
lib = dbl.Library().from_json_file('./example/library.json')

magic_items = lib.get_magic_items()
monsters = lib.get_monsters()
spells = lib.get_spells()
```

When extracting multiple types of content, it's faster to use the `get_content` function instead.

```python
content = lib.get_content(types=['magic items','spells'])
```

In all cases, what's returned is a list of content with each piece of content stored as an instance of the `ContentReference` class, which contains the following information:

 * **name.** the name of the content.
 * **id.** a string used by D&D Beyond when referring to the content.
 * **type.** either `magic item`, `monster`, or `spell`.
 * **path.** the location of the file the content was pulled from.
 * **modified.** when that file was last modified.
 * **sources.** a list of all books within the library the content can be found in.
 * **html.** a string containing the content's html description.


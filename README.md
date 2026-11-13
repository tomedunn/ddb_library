<!-- omit in toc -->
# ddb_library

This Python module provides tools for managing and parsing books from D&D Beyond in html form.

<!-- omit in toc -->
## Table of Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
- [File Structure](#file-structure)
- [Creating a New Library](#creating-a-new-library)
- [Saving a Library](#saving-a-library)
- [Loading an Existing Library](#loading-an-existing-library)
- [Updating an Existing Library](#updating-an-existing-library)
- [Copying an Existing Library](#copying-an-existing-library)
- [Extracting Book Contents](#extracting-book-contents)

## Installation
To use this module, download the `ddb_library` folder from this repository to your local machine.

If you are working in the same directory that folder is saved in then you should be able to load it directly. 
```python
import ddb_library
```
Otherwise, if the folder is save in a different location, you'll need to add the path to its location to Python.
```python
import sys
sys.path.append('path to directory containing ddb_library')

import ddb_library
```

### Dependencies
This module uses the following external Python libraries, which will need to be installed locally in order to work.

 * [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

## File Structure

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

For example, the url for the _D&D Beyond Basic Rules_ is [https://www.dndbeyond.com/sources/dnd/br-2024](https://www.dndbeyond.com/sources/dnd/br-2024) and so the folder for it is `./sources/br-2024`.

The file `sources.html` can have a different name, but that name will need to be specified when creating the library.

In rare cases, a book will also need sub-folders to hold component books or individual adventures. The names of these sub-folders must also follow the urls for those pages. For example, the url for the adventure "The Sunless Citadel" from _[Tales from the Yawning Portal](https://www.dndbeyond.com/sources/dnd/tftyp)_ is [https://www.dndbeyond.com/sources/dnd/tftyp/a1/the-sunless-citadel](https://www.dndbeyond.com/sources/dnd/tftyp/a1/the-sunless-citadel). In this case, the folder for the book would be `./sources/tftyp` and the sub-folder for the adventure would be `./sources/tftyp/a1`.

## Creating a New Library

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

## Saving a Library
A library can be saved locally using the following command.

```python
lib.save_json()
```

This stores the library as a `.json` file in the library's root directory. The default name of the file is `library.json`, but a different name can be specified if desired.

## Loading an Existing Library

A library that's been saved as a `.json` file can be loaded as follows.

```python
lib = dbl.Library().from_json_file('./example/library.json')
```

For large libraries, this is considerably faster than building the library from scratch each time.

## Updating an Existing Library
If the html files in an existing library are updated, or if new books are added, the library can be updated as follows.

```python
lib = dbl.Library().from_json_file('./example/library.json')
lib.update()
```

This will check each file to see if it has been modified since the last time recorded in `library.json`. If any of the files in a book have been updated then the whole book is reconstructed. Remember to save the library after updating.

## Copying an Existing Library

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

## Extracting Book Contents

This module contains functions for locating and extracting different kinds of content from an existing library, individual books, or pages. Currently, the following content types are supported:

* Encounter
* Figure
* Item
* Magic Item
* Monster
* Spell
* Table
* Treasure
* Vehicle

In some cases, content can be nested within another content type. For example, if a figure is within a monster stat block that figure will be included in the corresponding Monster content and won't show up as its own Figure content.

```python
import ddb_library as dbl

lib = dbl.Library().from_json_file('./example/library.json')

content = lib.get_content()
```

The content is returned as a `list` with a `dict` for each item containing the following fields:

 * **content_type.** the type of content from the list above.
 * **modified.** when that file was last modified.
 * **path.** the location of the file the content was pulled from.
 * **html.** a string containing the content's html description.
 * **book_path.** a string showing the items location within its respective book based on the book's headers.
 * **url.** the URL of the content's parent header on D&D Beyond.

Content can be processed further using the `ContentLibrary` class.

```python
clib = dbl.ContentLibrary(content)
```

This will attempt to convert each content type into a corresponding class by further processing its HTML. You can access this converted content through the content library's `contents` attribute. For example, to extract all successfully converted monsters,

```python
monsters = [c for c in clib.contents if type(c) is dbl.Monster]
```

You can use the `to_dict` class function to see the properties of any converted content.

```python
print(monsters[0].to_dict())
```

You can also use the `to_str` class function to convert most content types to a plain text format.

```python
print(monsters[0].to_str())
```
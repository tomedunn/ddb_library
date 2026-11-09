from bs4 import BeautifulSoup
import re

TAG_ATTRIBUTES = [
    'class', 'id', 'style', 'border', 'rowspan', 'colspan', 
    'width', 'height', 'align', 'valign', 'color', 'bgcolor', 
    'cellspacing', 'cellpadding', 'onclick', 'alt', 'title',
    'data-next-link','data-next-title',
    'data-prev-link','data-prev-title',
    'data-content-chunk-id', 'ata-content-chunk-id',
    'data-sheets-value', 
    'data-chapter-slug'
]

def cleanup_div(soup):
    re_reps = re.compile('\n')

    # remove empty <div>
    for data in soup(['div']):
        if data.text.strip() == '':
            data.decompose()
    
    # unwrap <div> if its only tag is another <div>
    for tag in soup.find_all('div'):
        if len([c for c in tag.contents if c.name]) != 1: continue
        for c in tag.contents:
            if c.name == 'div':
                tag.unwrap()
                break

    """for data in soup(['div']):
        if len([c for c in data.contents if c.name]) == 1:
            for c in data.contents:
                if c.name == 'div':
                    data.unwrap()
                    break"""
    
    # if <div> has only text inside it, put it all on one line.
    """for d in soup('div'):
        if len([c for c in d.contents if c.name != None]) == 0:
            d.string = re_reps.sub(' ', d.text.strip())"""
    
    for tag in soup.find_all('div'):
        if len([c for c in tag.contents if c.name != None]) == 0:
            tag.string = re_reps.sub(' ', tag.text.strip())
    
    return soup

def process_html(html_text, **kwargs):
    """
    Processes the given HTML text.

    Parameters
    ----------

    extract_main_body : bool
        If ``True`` a new simplified version of the page is constructed using just the main body 
        and a few useful elements from outside of it.
        Default value ``False``.

    remove_tags : list
        A list of tags to be removed. Tags may be given as either a string, in which case all tags with that name 
        are removed, or as a tuple containing the tag name and a dict of attributes and values that the tag must have
        in order to be removed.
        Default value ``[]``.
    
    unwrap_tags : list
        A list of tags to be unwrapped. Tags may be given as either a string, in which case all tags with that name 
        are unwrapped, or as a tuple containing the tag name and a dict of attributes and values that the tag must have
        in order to be removed.
        Default value ``[]``.
    
    remove_tag_attributes : list
        Removes the given attributes from all tags that have one.
        Default value ``[]``.
    
    cleanup_divs : bool
        If ``True`` then removes all div tags with no text inside them, unwraps all div tags that contain only a single
        div tag inside of them, and if a div tag contains only text then all the text is merged onto a single line.
        Default value ``False``.

    remove_empty_tags : list
        A list of tags to be removed if they contain no text inside of them. Tags may be given as either a string, in 
        which case all tags with that name are unwrapped, or as a tuple containing the tag name and a dict of attributes 
        and values that the tag must have in order to be removed.
        Default value ``[]``.
    
    remove_comments : bool
        If ``True`` then all comments are removed from the text.
        Default value ``False``.

    remove_blank_lines : bool
        If ``True`` then all lines of length zero are removed.
        Default value ``False``.
    
    replace_invisibles : bool
        If ``True`` then several non-standard white-space characters are replaced with a standard space character,
        and zero width characters are removed.
        Default value ``False``.
    
    replace_dashes : bool
        If ``True`` then several dash-like characters are replaced with standard dash characters ``-``.
        Default value ``False``.

    prettify : bool
        Applies several cosmetic changes to make the html text easier to read.
        Default value ``False``.

    Returns
    -------
    html_text : str
        The processed HTML text.
    """

    soup = BeautifulSoup(html_text, 'html.parser')
    
    if kwargs.get('extract_main_body', False):
        text = [kwargs.get('html_start', 
            '\n'.join(['<!DOCTYPE html>','<html lang="en-us">','<meta charset="utf-8"/>']),
        )]

        for link in soup.find_all('link', {'rel': 'canonical'}):
            text.append(str(link))
        
        for meta in soup.find_all('meta'):
            if meta.get('property', None) in ['og:title','og:type','og:url']:
                text.append(str(meta))

        #div = soup.find('div', {'class': ['main content-container','p-article-content','article-main']})
        div = soup.find('div', {'class': 'main content-container'})
        div = div if div else soup.find('div', {'id': 'S:0'})
        text.append(str(div) if div else '')
        text.append(kwargs.get('html_end', '</html>'))

        soup = BeautifulSoup('\n'.join(text), 'html.parser')
    
    # remove specific tags and their contents
    if kwargs.get('remove_tags', []):
        """tag_list = kwargs.get('remove_tags')
        for tag in soup.find_all(tag_list):
            tag.decompose()"""
        for item in kwargs.get('remove_tags'):
            if type(item) is tuple:
                for tag in soup.find_all(*item):
                    tag.decompose()
            else:
                for tag in soup.find_all(item):
                    tag.decompose()

    # remove specific tags but keep their contents
    if kwargs.get('unwrap_tags', []):
        for item in kwargs.get('unwrap_tags'):
            if type(item) is tuple:
                for tag in soup.find_all(*item):
                    tag.unwrap()
            else:
                for tag in soup.find_all(item):
                    tag.unwrap()

    # remove tag attributes
    if kwargs.get('remove_tag_attributes', []):
        attributes = kwargs.get('remove_tag_attributes')
        for attribute in attributes:
            if attribute in soup.attrs:
                soup.attrs.pop(attribute)
            [s.attrs.pop(attribute) for s in soup.find_all() if attribute in s.attrs]

    if kwargs.get('cleanup_divs', False):
        soup = cleanup_div(soup)

    # remove specific tags only if they're empty
    if kwargs.get('remove_empty_tags', []):
        for item in kwargs.get('remove_empty_tags'):
            if type(item) is tuple:
                for tag in soup.find_all(*item):
                    if tag.text.strip() == '':
                        tag.decompose()
            else:
                for tag in soup.find_all(item):
                    if tag.text.strip() == '':
                        tag.decompose()
    
    html_text = str(soup)

    if kwargs.get('remove_comments', False):
        html_text = re.sub(r'<!--.*-->[\r\n]', '', html_text)

    # remove blank lines
    if kwargs.get('remove_blank_lines', False):
        html_text = re.sub(r'[\r\n]+', '\n', html_text)
        html_text = '\n'.join([l for l in html_text.split('\n') if len(l) > 0])

    if kwargs.get('replace_invisibles', False):
        html_text = html_text.replace(' ', ' ') # replace invisible character U+00a0 with space.
        html_text = html_text.replace('­', '')   # replace invisible character U+00ad with nothing.

    if kwargs.get('replace_dashes', False):
        html_text = re.sub(r'[−–—]', '-', html_text) # replace dash characters U+2212 and U+2013 with dashes.

    if kwargs.get('prettify', False):
        html_text = re.sub(r'\s+(?=[\r\n])', '', html_text)                     # remove trailing spaces
        html_text = re.sub(r'(\s*<br/>\s*)+', '<br/>\n', html_text)             # ensure a <br/> is always followed by a new line and multiple aren't chained together
        html_text = re.sub(r'</div>(?=</div>)', '</div>\n', html_text)          # split multiple closed div tags across multiple lines.
        html_text = re.sub(r'<(\w+)> +', r'<\1>', html_text)                    # remove spaces after open tag 
        html_text = re.sub(r' +</(\w+)>', r'</\1>', html_text)                  # remove spaces before close tag 
        html_text = re.sub(r'[−–—]', '-', html_text)                            # replace dash characters U+2212 and U+2013 with dashes.
        html_text = re.sub(r'\s*<(li|p)>\s*', r'\n<\1>', html_text)             # put <li> and <p> tags at the start of their own line.
        html_text = re.sub(r'\s*</(li|p)>\s*', r'</\1>\n', html_text)           # put <li> and <p> tags at the start of their own line.
        html_text = re.sub(r'(?<!>)\n(?=[^<]+</p>)', '', html_text)             # makes sure paragraphs aren't broken up unnecessarily
        html_text = re.sub(r'\s*(</?blockquote>)\s*', r'\n\1\n', html_text)     # put <blockquote> tags on their own line
        html_text = re.sub(r'\s*(</?caption>)\s*', r'\n\1\n', html_text)        # put <caption> tags on their own line

    return html_text
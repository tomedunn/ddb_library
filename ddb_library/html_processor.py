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
    for data in soup(['div']):
        if len([c for c in data.contents if c.name]) == 1:
            for c in data.contents:
                if c.name == 'div':
                    data.unwrap()
                    break
    
    # if <div> has only text inside it, put it all on one line.
    for d in soup('div'):
        if len([c for c in d.contents if c.name != None]) == 0:
            d.string = re_reps.sub(' ', d.text.strip())
    
    return soup

def process_html(html_text, **kwargs):
    """
    options = {
        'cleanup_paragraphs': 'gets rid of paragraphs that are blank.',
        'cleanup_divs': 'does a few things, see function',
        'extract_main_body': 'keep only the main part of the page',
        'prettify': 'Makes the final text easier to read.',
        'remove_blank_lines': 'removes any blank lines from html text.',
        'remove_comments': 'removes any lines that are just a comment',
        'remove_empty_tags': 'removes any tag matching the tags in the given list that is also empty',
        'remove_tags': 'removes any tag matching the tags in the given list',
        'remove_tag_attributes': 'gets rid of the given attributes from any tag that has them',
        'replace_invisibles': 'replaces certain invisible characters with either a space or nothing.',
        'unwrap_tags': 'removes the given tags but keeps their contents',
    }
    """

    soup = BeautifulSoup(html_text, 'html.parser')
    
    if kwargs.get('extract_main_body', False):
        text = [kwargs.get('html_start', 
            '\n'.join(['<!DOCTYPE html>','<html lang="en-us">','<meta charset="utf-8"/>']),
        )]

        for meta in soup.find_all('meta'):
            if meta.get('property', None) in ['og:title','og:type','og:url']:
                text.append(str(meta))

        #div = soup.find('div', {'class': ['main content-container','p-article-content','article-main']})
        div = soup.find('div', {'class': 'main content-container'})
        text.append(str(div) if div else '')
        text.append(kwargs.get('html_end', '</html>'))

        soup = BeautifulSoup('\n'.join(text), 'html.parser')
    
    # remove specific tags only if they're empty
    if kwargs.get('remove_empty_tags', []):
        """tag_list = kwargs.get('remove_empty_tags')
        for tag in soup.find_all(tag_list):
            if tag.text.strip() == '':
                tag.decompose()"""
        for item in kwargs.get('remove_empty_tags'):
            if type(item) is tuple:
                for tag in soup.find_all(*item):
                    if tag.text.strip() == '':
                        tag.decompose()
            else:
                for tag in soup.find_all(item):
                    if tag.text.strip() == '':
                        tag.decompose()
    
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
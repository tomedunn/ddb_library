def flatten_content(nested_contents, content_path=[], content=None):
    if content == None: content = []
    if type(nested_contents) is list:
        for nested_content in nested_contents:
            content = flatten_content(nested_content, content_path, content)
    else:
        content_path.append(nested_contents['name'])
        for c in nested_contents['contents']:
            c['book_path'] = ';'.join(content_path)
            c['url'] = nested_contents['url']
            content.append(c.copy())
        content = flatten_content(nested_contents.get('children', []), content_path, content)
        content_path.pop(-1)
    return content
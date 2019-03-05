import re

import pytest

from helpers import href_is_valid_url, remove_non_local_urls, handle_relative_paths


@pytest.mark.parametrize('href, valid', (
    ('http://www.example.com', True),
    ('https://www.example.com', True),
    ('http://example.com', True),
    ('http://beta.example.com', True),
    ('http://www.example.com/', True),
    ('https://200.200.200.200:443', True),
    ('http://www.example .com', False),
    ('mailto:me@example.com', False),
    ('', False),
    (None, False),
    ('+4478565161123', False),
))
def test_href_is_valid_url(href, valid):
    assert href_is_valid_url(href) == valid


def test_remove_non_local_urls():
    website_domain_pattern = re.compile('^(http|https)://{}.*$'.format('www.example.com/'))
    local_urls = {
        'https://www.example.com/dir_1/doc.html',
        'https://www.example.com/',
        'https://www.example.com/dir_1/dir_2/doc_2.html?query=1#3'
    }
    non_local_urls = {
        'https://example.com/dir_1/doc.html',
        'https://www.example2.com/',
        'https://beta.example.com/dir_1/dir_2/doc_2.html?query=1#3'
    }
    urls = local_urls.union(non_local_urls)
    assert remove_non_local_urls(urls, website_domain_pattern) == local_urls


def test_handle_relative_paths():
    parent = 'https://www.example.com/doc_1.html'
    children = {'https://www.example.com/doc_2.html','doc_3.html'}
    result = {'https://www.example.com/doc_2.html', 'https://www.example.com/doc_3.html'}

    assert handle_relative_paths(parent, children) == result

from time import sleep, time
from urllib.parse import urlparse, urljoin

import re
from typing import Pattern, Set


valid_url_pattern = re.compile(r"^(?:http(s)?://)?[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'\(\)\*\+,;=]+$")
allow_pattern = re.compile(r'^Allow:\s+(.+)$')
disallow_pattern = re.compile(r'^Disallow:\s+(.+)$')
user_agent_pattern = re.compile(r'^User-agent:\s+(.+)$')


class RateLimit:

    def __init__(self, *, max_rate: int) -> None:
        self.time_between_actions = 1 / max_rate
        self.last_action_time = time() - self.time_between_actions

    def __call__(self, wrapped_function):
        def wrapper(*args, **kwargs):
            wait_for_time = self.last_action_time + self.time_between_actions - time()
            if wait_for_time > 0:
                sleep(wait_for_time)
            self.last_action_time = time()
            return wrapped_function(*args, **kwargs)

        return wrapper


def href_is_valid_url(href: str):
    """
    First make sure the href is a non-empty string. This is necessary because there are quite a few <a> tags with no
    href attribute. If that test pasts, explicitly match against valid_url_pattern. This avoids non-url hrefs, e.g.,
    phone numbers, email addresses and so on
    """
    return isinstance(href, str) and href != '' and valid_url_pattern.match(href)


def convert_to_regex(raw_pattern: str) -> Pattern[str]:
    """
    The robots.txt provides rules like:

    Allow: */data/*.html

    We would like to match new paths we find against these, which is slightly messy. Need to make sure to escape
    anything like '+' or '.' which is a safe url character, but which might be misconstrued as a regex operator.
    Also, need to replace the robots.txt version of the wildcard with '.*'. Finally, there might be a rule like:

    Disallow: /data/

    Which would recursively disallow everything inside the data directory...we can just make the replacement
    '/' --> '/*' and then apply the rules above.
    """
    if raw_pattern.endswith('/'):
        raw_pattern += '*'
    pattern = re.escape(raw_pattern).replace('\\*', '.*')
    return re.compile('^' + pattern + '$')


def remove_non_local_urls(urls: Set[str], local_domain: Pattern[str]) -> Set[str]:
    local_urls = set()
    for url in urls:
        if local_domain.match(url):
            local_urls.add(url)
    return local_urls


def handle_relative_paths(parent_url: str, child_urls: Set[str]):
    fully_qualified_urls = set()
    for child_url in child_urls:
        parsed_child = urlparse(child_url)
        if not parsed_child.netloc:
            # To trigger this condition, our child_url *probably* has the form 'doc.html'. It's also possible the url
            # is broken.
            fully_qualified_urls.add(urljoin(parent_url, child_url))
        else:
            fully_qualified_urls.add(child_url)
    return fully_qualified_urls

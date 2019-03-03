from typing import Pattern, List

from abc import ABCMeta, abstractmethod

import re
from bs4 import BeautifulSoup

from requests import Session
from requests.models import Response

user_agent_pattern = re.compile(r'^User-agent:\s+(.+)$')
allow_pattern = re.compile(r'^Allow:\s+(.+)$')
disallow_pattern = re.compile(r'^Disallow:\s+(.+)$')
local_domain = re.compile('^(http|https)://www.thomann.de.*$')


def _convert_to_regex(raw_pattern: str) -> Pattern[str]:
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


class RobotRule:
    def __init__(self, root_url: str, raw_path: str, allow: bool) -> None:
        """
        :param root_url: The root of the website, including domain and schema, e.g. http://www.example.com
        :param raw_path: A rule from the robots.txt, excluding its key...e.g., if a line in the file looks like:

                         Allow: /books.html

                         then raw_path == '/books.html'
        :param allow: Whether the rule is telling us to 'Allow: ...' (True) or 'Disallow: ...'
        """
        self._pattern = _convert_to_regex(root_url + raw_path)
        self.allow = allow
        self._priority = len(raw_path)

    def __ge__(self, other: "RobotRule") -> bool:
        """
        "At a group-member level, in particular for allow and disallow directives, the most specific rule based on the
        length of the [path] entry will trump the less specific (shorter) rule. The order of precedence for rules with
        wildcards is undefined."
        see https://developers.google.com/search/reference/robots_txt

        With this in mind, we have defined self._priority to represent the length of the rule, and will compare them
        to see which rule wins.
        """
        if not isinstance(other, self.__class__):
            raise TypeError(f"'>=' not supported between instances of {other.__class__} and {self.__class__}.")

        return self._priority >= other._priority

    def match(self, string):
        return self._pattern.match(string)

    @classmethod
    def factory(cls, root_url: str, rule) -> "RobotRule":
        allow_match = allow_pattern.match(rule)
        disallow_match = disallow_pattern.match(rule)

        if allow_match:
            new_rule = cls(root_url=root_url, raw_path=allow_match.group(1), allow=True)
        else:
            new_rule = cls(root_url=root_url, raw_path=disallow_match.group(1), allow=False)

        return new_rule

    @property
    def priority(self) -> int:
        """
        The 'priority' corresponds to the length of the path and is used for determining the order in which rules
        should be applied
        """
        return self._priority


class BaseRobotsParser(metaclass=ABCMeta):
    """
    We're going to implement our robots.txt parser as a mixin, so we'd better build it on top of an abstract base class
    so alternative parsers implement the same API in the future.
    """
    @abstractmethod
    def parse_robots(self):
        pass


class RobotsParser(BaseRobotsParser):
    """
    May as well make this a mixin so we can switch out our robots policy if we want. The RobotsParser policy is:
       1. Ignore all user-agent rules more personalised than 'User-agent: *' (we aren't that famous!)
       2. Ignore sitemaps
       3. Observe all other rules
    """

    def _get_robots(self):
        return self.get_content_as_text(self._website_root + 'robots.txt')

    def _filter_by_agent(self, robots_rules):
        """
        Get the set of rules in the scope of our user agent. The user-agents we match are defined by
        self.relevant_agents
        """
        relevant_rules = []  # i.e. rules applicable to '*' user-agent...see docstring

        in_relevant_group = False
        for rule in robots_rules:
            user_agent_match = user_agent_pattern.match(rule)
            if user_agent_match:
                in_relevant_group = True if user_agent_match.group(1) in self.relevant_agents else False
            elif in_relevant_group:
                # We want to exclude empty lines, comments, site map etc
                if any([pattern.match(rule) for pattern in (allow_pattern, disallow_pattern)]):
                    new_rule = RobotRule.factory(self._website_root, rule)
                    relevant_rules.append(new_rule)

        return relevant_rules

    @staticmethod
    def _sort_robots_by_priority_decreasing(relevant_rules: List[RobotRule]):
        relevant_rules.sort(key=lambda rule: rule.priority, reverse=True)

    def parse_robots(self):
        robots_rules = self._get_robots().splitlines()
        relevant_rules = self._filter_by_agent(robots_rules)
        self._sort_robots_by_priority_decreasing(relevant_rules)
        return relevant_rules


class BaseClient:
    _url_template = '{}/{}'

    def __init__(self, website_root: str, schema: str) -> None:
        # Instantiate a TCP pool to reduce syn/syn-ack overhead
        self._session = Session()
        self._website_root = website_root

    def _get(self, url: str) -> Response:
        return self._session.get(url)

    # def _get_path(self, path: str) -> Response:
    #     return self._get(self._url_template.format(self._website_root, path))

    def get_content_as_text(self, url: str) -> str:
        return self._get(url).text


class Aragog(RobotsParser, BaseClient):
    relevant_agents = ('*',)  # The user agents our crawler matches

    def __init__(self, website_root: str, schema: str='http') -> None:
        super().__init__(website_root, schema)
        self.robots = self.parse_robots()
        self._crawled_urls = set()
        self._scheduled_urls = set()

    def get_child_urls_from_parent(self, parent_url):
        page_contents = self.get_content_as_text(parent_url)
        parsed_contents = BeautifulSoup(page_contents, 'html.parser')
        a_tags = parsed_contents.find_all('a')
        hrefs = {a_tag.get('href') for a_tag in a_tags}

        # Make sure the href is a non-empty string. Could probably simplify this somewhat by making the lambda
        # simply check if the href has a truthy boolean value, but I just want to make sure there isn't some edge case
        # I didn't account for basically...
        urls = filter(lambda href: isinstance(href, str) and href is not '', hrefs)
        local_urls = set()
        for url in urls:
            if local_domain.match(url):
               local_urls.add(set)

        return local_urls

    def schedule_urls(self, *urls):
        for url in urls:
            self._scheduled_urls.add(url)

    def crawl(self):
        self.schedule_urls(self._website_root)
        while self._scheduled_urls:
            next_url = self._scheduled_urls.pop()
            scraped_urls = self.get_child_urls_from_parent(next_url)
            self._crawled_urls.add(next_url)
            urls_to_schedule = scraped_urls - self._crawled_urls




if __name__ == '__main__':
    aragog = Aragog('http://www.thomann.de')
    aragog.crawl()

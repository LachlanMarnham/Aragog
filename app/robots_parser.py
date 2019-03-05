from typing import List
from abc import ABCMeta, abstractmethod

from requests.exceptions import SSLError

from helpers import convert_to_regex, allow_pattern, disallow_pattern, user_agent_pattern


class RobotRule:
    def __init__(self, root_url: str, raw_path: str, allow: bool) -> None:
        """
        :param root_url: The root of the website, including domain and schema, e.g. http://www.example.com
        :param raw_path: A rule from the robots.txt, excluding its key...e.g., if a line in the file looks like:

                         Allow: /books.html

                         then raw_path == '/books.html'
        :param allow: Whether the rule is telling us to 'Allow: ...' (True) or 'Disallow: ...'
        """
        self._pattern = convert_to_regex(root_url + raw_path)
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


# TODO quite a bit of the parsing I implemented can be avoided by urllib.robotparser (which I was unaware of...)
class RobotsParser(BaseRobotsParser):
    """
    May as well make this a mixin so we can switch out our robots policy if we want. The RobotsParser policy is:
       1. Ignore all user-agent rules more personalised than 'User-agent: *' (we aren't that famous!)
       2. Ignore sitemaps
       3. Observe all other rules
    """

    def _get_robots(self):
        return self.get_content_as_text(self.website_root + 'robots.txt')

    def _filter_by_agent(self, robots_rules: List[str]) -> List[str]:
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
                    new_rule = RobotRule.factory(self.website_root, rule)
                    relevant_rules.append(new_rule)

        return relevant_rules

    @staticmethod
    def _sort_robots_by_priority_decreasing(relevant_rules: List[RobotRule]):
        relevant_rules.sort(key=lambda rule: rule.priority, reverse=True)

    def parse_robots(self):
        try:
            robots_rules = self._get_robots().splitlines()
        except SSLError:  # Not every website has a robots.txt file...
            robots_rules = []
        relevant_rules = self._filter_by_agent(robots_rules)
        self._sort_robots_by_priority_decreasing(relevant_rules)
        return relevant_rules

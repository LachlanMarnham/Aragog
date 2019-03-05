import pytest

from aragog import Aragog
from robots_parser import RobotRule, RobotsParser


class TestRobotRule:
    def test_allowed(self):
        rule = RobotRule.factory('http://www.example.com', 'Allow: */classified_category*?pg=')
        assert rule.allow is True

    def test_disallowed(self):
        rule = RobotRule.factory('http://www.example.com', 'Disallow: */classified_category*&wghky')
        assert rule.allow is False

    @pytest.mark.parametrize('raw_rule, url', (
            ('Disallow: /books/', 'http://www.example.com/books/d3sIgn_p4tt3rn5'),
            ('Disallow: /bkshp?*q=*', 'http://www.example.com/bkshp?fq=1'),
            ('Allow: /?hl=*&*&gws_rd=ssl', 'http://www.example.com/?hl=23423&something_here&gws_rd=ssl'),
            ('Allow: *imode', 'http://www.example.com/path_1/path_2/imode'),
            ('Disallow: */prod_embeddedcbundle*.html', 'http://www.example.com/path_1/prod_embeddedcbundle21.html')
    ))
    def test_rule_path_match(self, raw_rule, url):
        rule = RobotRule.factory('http://www.example.com', raw_rule)
        assert rule.match(url)

    @pytest.mark.parametrize('raw_rule, url', (
            ('Allow: *imode', 'https://www.example.com/path_1/path_2/imode'),  # different scheme
            ('Allow: *imode', 'http://beta.example.com/path_1/path_2/imode'),  # Different subdomain prefix
            ('Allow: *imode', 'http://example.com/path_1/path_2/imode'),  # No sub-domain prefix
            ('Allow: *imode', 'http://www.example.com/path_1/path_2/imode2'),  # With trailing characters
    ))
    def test_rule_path_doesnt_match(self, raw_rule, url):
        rule = RobotRule.factory('http://www.example.com', raw_rule)
        assert not rule.match(url)

    @pytest.mark.parametrize('rule_1, rule_2, result', (
        ('Allow: aa', 'Allow: a', True),
        ('Allow: aa', 'Allow: aa', True),
        ('Allow: a', 'Allow: aa', False),
        ('Disallow: aa', 'Disallow: a', True),
        ('Disallow: aa', 'Disallow: aa', True),
        ('Disallow: a', 'Disallow: aa', False),
    ))
    def test_rule_priority_comparison(self, rule_1, rule_2, result):
        lhs = RobotRule.factory('http://www.example.com', rule_1)
        rhs = RobotRule.factory('http://www.example.com', rule_2)
        assert (lhs >= rhs) is result


class TestRobotsParser:
    """
    For all of the tests in this class, we mock out the request to http://www.example.com/robots.txt to return
    example_robots_txt
    """
    def test_robots_well_ordered(self, mocker, example_robots_txt):
        RobotsParser._get_robots = mocker.MagicMock(return_value=example_robots_txt)
        aragog = Aragog('www.example.com', 'http://', plot_output=False)
        robots_list = aragog.robots

        for i in range(1, len(robots_list)):
            assert robots_list[i - 1] >= robots_list[i]

    def test_found_five_relevant_rules(self, mocker, example_robots_txt):
        RobotsParser._get_robots = mocker.MagicMock(return_value=example_robots_txt)
        aragog = Aragog('www.example.com', 'http://', plot_output=False)
        assert len(aragog.robots) == 5

    def test_allowed_disallowed(self, mocker, example_robots_txt):
        RobotsParser._get_robots = mocker.MagicMock(return_value=example_robots_txt)
        aragog = Aragog('www.example.com', 'http://', plot_output=False)

        # Should be 4 'Disallow: ...' rules
        assert len([rule for rule in aragog.robots if rule.allow is False]) == 4

        # Should be 1 'Allow: ...' rule
        assert len([rule for rule in aragog.robots if rule.allow is True]) == 1

import os.path
import sys

import pytest

base_path = os.path.abspath('..')
aragog_app = os.path.join(base_path, 'app')
sys.path.insert(0, aragog_app)

from aragog import RobotRule


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
            ('Allow: *imode', 'http://example.com/path_1/path_2/imode'),  # No subdomain prefix
            ('Allow: *imode', 'http://www.example.com/path_1/path_2/imode2'),  # With trailing characters
    ))
    def test_rule_path_doesnt_match(self, raw_rule, url):
        rule = RobotRule.factory('http://www.example.com', raw_rule)
        assert not rule.match(url)


import pytest


@pytest.fixture(scope="module")
def example_robots_txt():
    return """User-agent: *
Disallow: /asdfasdf.html
Disallow: /pics/lisdad/
Disallow: */restrict*?wghky
Disallow: */restrict*&wghky
Allow: */restrict*?pg=

Sitemap: https://www.example.com/sitemap.xml

User-agent: AdsBot-Google-Mobile-Apps
Allow: /intl/"""
from typing import Set
import re
from bs4 import BeautifulSoup

from requests import Session, Response

from helpers import RateLimit, href_is_valid_url, handle_relative_paths, remove_non_local_urls
from network_grapher import NetworkGraphHandler
from robots_parser import RobotsParser


class BaseClient:
    def __init__(self, website_root: str) -> None:
        # Instantiate a TCP pool to reduce syn/syn-ack overhead
        self._session = Session()
        self.website_root = website_root

    @RateLimit(max_rate=2)
    def _get(self, url: str) -> Response:
        return self._session.get(url)

    def get_content_as_text(self, url: str) -> str:
        return self._get(url).text


class Aragog(RobotsParser, BaseClient):
    relevant_agents = ('*',)  # The user agents our crawler matches

    def __init__(self, website_domain: str, schema: str, plot_output: bool) -> None:
        website_root = schema + website_domain
        self._website_domain_pattern = re.compile('^(http|https)://{}.*$'.format(website_domain))
        super().__init__(website_root)
        self.robots = self.parse_robots()
        self._crawled_urls = set()  # The pages we already visited
        self._seen_urls = set()  # The pages we have found links to, but don't necessarily want to visit
        self._scheduled_urls = set()  # The pages we intend to visit

        # Triggered by the --plot_output flag at runtime
        self._plot_handler = NetworkGraphHandler() if plot_output else None

    def get_child_urls_from_parent(self, parent_url):
        page_contents = self.get_content_as_text(parent_url)
        parsed_contents = BeautifulSoup(page_contents, 'html.parser')
        a_tags = parsed_contents.find_all('a')
        hrefs = {a_tag.get('href') for a_tag in a_tags}

        # Make sure the href is a non-empty string. Could probably simplify this somewhat by making the lambda
        # simply check if the href has a truth-y boolean value, but I just want to make sure there isn't some edge case
        # I didn't account for basically...
        urls = set(filter(href_is_valid_url, hrefs))

        # Some of the tags will have relative hrefs, like <a href="data.html">...</a>. We want to handle this by
        # doing a join with the parent
        fully_qualified_urls = handle_relative_paths(parent_url, urls)
        return fully_qualified_urls

    def schedule_url(self, url: str) -> None:
        self._scheduled_urls.add(url)

    def schedule_allowed_urls(self, local_urls):
        for url in local_urls:
            for robot_rule in self.robots:
                if robot_rule.match(url):
                    if robot_rule.allow:
                        self.schedule_url(url)
                    else:
                        break
            # We get here if we didn't match any robots.txt rules. Assume we can scrape the page
            self.schedule_url(url)

    def choose_url_and_scrape(self):
        next_url = self._scheduled_urls.pop()
        scraped_urls = self.get_child_urls_from_parent(next_url)
        self._crawled_urls.add(next_url)
        if self._plot_handler is not None:
            self._add_new_edges(parent=next_url, children=scraped_urls)
        return scraped_urls - self._seen_urls

    def _add_new_edges(self, parent, children):
        for child in children:
            self._plot_handler.draw_updated_graph(parent, child)

    def _mark_urls_as_seen(self, *urls):
        for url in urls:
            self._seen_urls.add(url)

    def output_scraped_urls(self, urls: Set[str]) -> None:
        """
        Ok...this isn't very exciting. I've just wrapped the call to print so the code is a bit more fragmented.
        In this case the idea is that instead of printing our urls to stout (not very useful!) we can instead log them
        or write them to a DB by switching out just one method.
        We don't log any of the urls that we have seen before.
        """
        for url in urls.difference(self._seen_urls):
            print(url)

    def crawl(self):
        self.schedule_url(self.website_root)
        while self._scheduled_urls:
            # choose_url_and_scrape() will only return urls we haven't seen yet
            new_urls = self.choose_url_and_scrape()

            # Output all of the urls we haven't seen before, whether they are local or not
            self.output_scraped_urls(new_urls)
            self._mark_urls_as_seen(*new_urls)

            # Schedule all the new_urls we just scraped if 1) they are from the local domain, and 2) they follow the
            # rules from the robots.txt
            local_urls = remove_non_local_urls(new_urls, self._website_domain_pattern)

            self.schedule_allowed_urls(local_urls)

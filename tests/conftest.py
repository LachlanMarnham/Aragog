import pytest


@pytest.fixture(scope="module")
def example_robots_txt():
    with open('test_data/robots.txt') as file:
        contents = file.read()
    return contents

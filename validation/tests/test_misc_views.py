import urllib.robotparser
from http import HTTPStatus


def test_robots_txt_is_served(client):
    """
    We should be able to get /robots.txt and parse it.
    """

    r = client.get("/robots.txt")
    assert r.status_code == HTTPStatus.OK

    robots_txt = r.content.decode("UTF-8")

    # The RobotFileParser has an... interesting... API
    # See: https://docs.python.org/3/library/urllib.robotparser.html
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots_txt.splitlines())

    assert rp.can_fetch("Googlebot/2.1", "/") is False

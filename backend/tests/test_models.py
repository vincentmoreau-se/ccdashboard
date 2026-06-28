from app.models import Usage


def test_usage_add():
    a = Usage(input=10, output=5, cache_read=2)
    b = Usage(input=1, output=1, web_search=3)
    c = a.add(b)
    assert c.input == 11
    assert c.output == 6
    assert c.cache_read == 2
    assert c.web_search == 3

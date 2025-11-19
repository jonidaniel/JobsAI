import pytest
from urllib.parse import urlparse, parse_qs

from utils.query_builder import build_duunitori_query

# ---------------------------------------------------
# 1. Single keyword
# ---------------------------------------------------
def test_single_keyword_query():
    url = build_duunitori_query(["python"])
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert "python" in params.get("search", [""])[0]


# ---------------------------------------------------
# 2. Multiple keywords
# ---------------------------------------------------
def test_multiple_keywords_query():
    url = build_duunitori_query(["python", "developer"])
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert "python developer" in params.get("search", [""])[0]


# ---------------------------------------------------
# 3. Special characters encoded correctly
# ---------------------------------------------------
def test_query_encoding_special_chars():
    url = build_duunitori_query(["c++", "näkö"])
    assert "c%2B%2B" in url
    assert "n%C3%A4k%C3%B6" in url


# ---------------------------------------------------
# 4. Location parameter appears when provided
# ---------------------------------------------------
def test_location_added():
    url = build_duunitori_query(["python"], location="helsinki")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert params.get("location", [""])[0] == "helsinki"


# ---------------------------------------------------
# 5. Pagination
# ---------------------------------------------------
def test_pagination_parameter():
    url = build_duunitori_query(["python"], page=3)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert params.get("page", [""])[0] == "3"


# ---------------------------------------------------
# 6. Default behavior for empty keywords
# ---------------------------------------------------
def test_default_keyword_behavior():
    url = build_duunitori_query([])
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert "search" in params
    assert params["search"][0] != ""  # Should fall back to something meaningful


# ---------------------------------------------------
# 7. Invalid input
# ---------------------------------------------------
def test_invalid_keyword_input():
    with pytest.raises(ValueError):
        build_duunitori_query(None)


# ---------------------------------------------------
# 8. Platform-specific rules
# Duunitori uses 'search', not 'haku'
# ---------------------------------------------------
def test_duunitori_uses_search_param():
    url = build_duunitori_query(["python"])

    assert "search=" in url
    assert "haku=" not in url


# ---------------------------------------------------
# 9. Snapshot test (optional)
# ---------------------------------------------------
def test_query_snapshot(snapshot):
    url = build_duunitori_query(
        ["python", "developer"],
        page=2,
        location="helsinki"
    )
    snapshot.assert_match(url)

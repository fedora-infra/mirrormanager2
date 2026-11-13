import pytest

from mirrormanager2.utility.pagination import PagedResult


@pytest.mark.parametrize(
    "total,page_number,expected",
    [
        pytest.param(30, 2, [1, 2, 3], id="few-pages"),
        pytest.param(200, 1, [1, 2, 3, 4, 5, 6, 7, 8, 9, None, 20], id="start"),
        pytest.param(200, 10, [1, None, 6, 7, 8, 9, 10, 11, 12, 13, 14, None, 20], id="middle"),
        pytest.param(200, 19, [1, None, 12, 13, 14, 15, 16, 17, 18, 19, 20], id="end"),
    ],
)
def test_truncated_pages_list(total, page_number, expected):
    result = PagedResult(total=total, page_size=10, page_number=page_number)
    assert result.truncated_pages_list(margin=4) == expected

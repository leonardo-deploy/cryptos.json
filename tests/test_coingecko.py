from unittest.mock import Mock, patch

import pytest

from src.coingecko import CoinGeckoClient


def _response(payload: object, status: int = 200) -> Mock:
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_fetch_continues_when_a_page_is_short_or_empty() -> None:
    session = Mock()
    session.headers = {}
    session.get.side_effect = [_response([{"id": "bitcoin"}]), _response([])]
    client = CoinGeckoClient(session=session)

    with patch("src.coingecko.time.sleep") as sleep:
        result = client.fetch_markets(pages=2, per_page=250, delay_seconds=30)

    assert result == [{"id": "bitcoin"}]
    assert session.get.call_count == 2
    sleep.assert_called_once_with(30)


def test_fetch_explains_rate_limit() -> None:
    session = Mock()
    session.headers = {}
    session.get.side_effect = [_response([], status=429), _response([])]
    client = CoinGeckoClient(session=session)

    with patch("src.coingecko.time.sleep") as sleep:
        result = client.fetch_markets(pages=1)

    assert result == []
    assert session.get.call_count == 2
    sleep.assert_called_once_with(60)


def test_fetch_enforces_page_and_delay_limits() -> None:
    client = CoinGeckoClient(session=Mock(headers={}))

    with pytest.raises(ValueError, match="entre 1 e 80"):
        client.fetch_markets(pages=81)

    with pytest.raises(ValueError, match="pelo menos 30 segundos"):
        client.fetch_markets(pages=2, delay_seconds=29)

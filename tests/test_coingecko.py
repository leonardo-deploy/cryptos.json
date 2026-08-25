from unittest.mock import Mock

import pytest

from src.coingecko import CoinGeckoClient, CoinGeckoError


def _response(payload: object, status: int = 200) -> Mock:
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_fetch_stops_when_last_page_is_short() -> None:
    session = Mock()
    session.headers = {}
    session.mount = Mock()
    session.get.return_value = _response([{"id": "bitcoin"}])
    client = CoinGeckoClient(session=session)

    result = client.fetch_markets(pages=5, per_page=250, delay_seconds=30)

    assert result == [{"id": "bitcoin"}]
    session.get.assert_called_once()


def test_fetch_explains_rate_limit() -> None:
    session = Mock()
    session.headers = {}
    session.mount = Mock()
    session.get.return_value = _response([], status=429)
    client = CoinGeckoClient(session=session)

    with pytest.raises(CoinGeckoError, match="limite temporário"):
        client.fetch_markets()


def test_fetch_enforces_page_and_delay_limits() -> None:
    client = CoinGeckoClient(session=Mock(headers={}, mount=Mock()))

    with pytest.raises(ValueError, match="entre 1 e 80"):
        client.fetch_markets(pages=81)

    with pytest.raises(ValueError, match="pelo menos 30 segundos"):
        client.fetch_markets(pages=2, delay_seconds=29)

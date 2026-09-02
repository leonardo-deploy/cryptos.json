from unittest.mock import Mock, patch

import pytest

from src.coingecko import CoinGeckoClient, FetchProgress


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
    assert sleep.call_count == 30
    sleep.assert_called_with(1)


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

    with pytest.raises(ValueError, match="entre 1 e 40"):
        client.fetch_markets(pages=41)

    with pytest.raises(ValueError, match="exatamente 250"):
        client.fetch_markets(per_page=249)

    with pytest.raises(ValueError, match="pelo menos 30 segundos"):
        client.fetch_markets(pages=2, delay_seconds=29)

    with pytest.raises(ValueError, match="pelo menos 60 segundos"):
        client.fetch_markets(block_delay_seconds=59)


def test_fetch_reports_page_and_block_countdowns() -> None:
    session = Mock()
    session.headers = {}
    session.get.side_effect = [_response([{"id": f"coin-{page}"}]) for page in range(1, 6)]
    client = CoinGeckoClient(session=session)
    events: list[FetchProgress] = []

    with patch("src.coingecko.time.sleep") as sleep:
        client.fetch_markets(
            pages=5,
            delay_seconds=30,
            progress_callback=events.append,
        )

    assert any(event.wait_label == "Intervalo entre páginas" and event.wait_seconds == 30 for event in events)
    assert any(event.wait_label == "Pausa após bloco de 4 páginas" and event.wait_seconds == 60 for event in events)
    assert sleep.call_count == 180

import json

import pytest

from subsurfer.core.handler.passive.freecampdev import FreecampDevScanner


class MockResponse:
    def __init__(self, status, text):
        self.status = status
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def text(self):
        return self._text


class MockSession:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def post(self, *args, **kwargs):
        return self.response


@pytest.mark.asyncio
async def test_freecampdev_scanner_returns_valid_results(monkeypatch):
    domain = "example.com"
    payload = json.dumps(
        {
            "results": [
                {"subdomain": f"www.{domain}"},
                {"subdomain": f"api.{domain}"},
                {"subdomain": "invalid.test"},
            ]
        }
    )

    monkeypatch.setattr(
        "subsurfer.core.handler.passive.freecampdev.aiohttp.ClientSession",
        lambda: MockSession(MockResponse(200, payload)),
    )

    scanner = FreecampDevScanner(domain, silent=True)
    results = await scanner.scan()

    assert results == {f"www.{domain}", f"api.{domain}"}


@pytest.mark.asyncio
async def test_freecampdev_scanner_skips_false_positive_over_threshold(monkeypatch):
    domain = "example.com"
    payload = json.dumps(
        {
            "results": [
                {"subdomain": f"sub{i}.{domain}"}
                for i in range(FreecampDevScanner.MAX_SUBDOMAINS + 1)
            ]
        }
    )

    monkeypatch.setattr(
        "subsurfer.core.handler.passive.freecampdev.aiohttp.ClientSession",
        lambda: MockSession(MockResponse(200, payload)),
    )

    scanner = FreecampDevScanner(domain, silent=True)
    results = await scanner.scan()

    assert results == set()

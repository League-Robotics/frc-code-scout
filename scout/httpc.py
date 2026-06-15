"""Minimal HTTP+cache client over urllib — no third-party deps.

get_json() fetches and decodes JSON with: User-Agent, optional bearer auth,
retry-with-backoff on transient errors, GitHub rate-limit awareness, and an
optional on-disk JSON cache so reruns don't re-hit the network.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import config


class HttpError(Exception):
    """Carries the HTTP status so callers can special-case 404 etc."""

    def __init__(self, status: int, url: str, body: str = ""):
        super().__init__(f"HTTP {status} for {url}")
        self.status = status
        self.url = url
        self.body = body


def _read_cache(cache_path: Path | None):
    if cache_path and cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _write_cache(cache_path: Path | None, data) -> None:
    if not cache_path:
        return
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(data))
    except OSError:
        pass  # caching is best-effort


def get_json(
    url: str,
    *,
    token: str | None = None,
    cache_path: Path | None = None,
    accept: str = "application/json",
    retries: int = 4,
    pause: float = 0.0,
):
    """GET `url` and decode JSON.

    Returns the parsed object. Raises HttpError(status) for HTTP error responses
    (callers handle 404). Uses cache_path if present; writes it on success.
    """
    cached = _read_cache(cache_path)
    if cached is not None:
        return cached

    headers = {"User-Agent": config.USER_AGENT, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_exc: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                _respect_rate_limit(resp.headers)
                data = json.loads(resp.read().decode("utf-8"))
            _write_cache(cache_path, data)
            if pause:
                time.sleep(pause)
            return data
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:500]
            except Exception:
                pass
            if e.code == 404:
                raise HttpError(404, url, body) from e
            if e.code in (403, 429):  # rate-limited / abuse — back off on reset
                _respect_rate_limit(e.headers)
            if e.code < 500 and e.code not in (403, 429):
                raise HttpError(e.code, url, body) from e
            last_exc = HttpError(e.code, url, body)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_exc = e
        time.sleep(min(2 ** attempt, 30))  # exponential backoff

    if isinstance(last_exc, Exception):
        raise last_exc
    raise HttpError(0, url, "exhausted retries")


def _respect_rate_limit(headers) -> None:
    """If GitHub says we're out of requests, sleep until the reset time."""
    remaining = headers.get("X-RateLimit-Remaining")
    reset = headers.get("X-RateLimit-Reset")
    if remaining is None or reset is None:
        return
    try:
        if int(remaining) <= 1:
            wait = max(0, int(reset) - int(time.time())) + 2
            if 0 < wait <= 3600:
                print(f"[scout] GitHub rate limit reached; sleeping {wait}s")
                time.sleep(wait)
    except (ValueError, TypeError):
        pass

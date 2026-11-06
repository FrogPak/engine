"""Small HTTP helpers on urllib, so the engine needs no third-party HTTP library."""
import json
import shutil
import time
import urllib.error
import urllib.request

USER_AGENT = "FrogPak"
ATTEMPTS = 3


class HTTPError(Exception):
    def __init__(self, url, status, message=""):
        self.url = url
        self.status = status
        super().__init__(f"{url}: HTTP {status} {message}".rstrip())


class NetworkError(Exception):
    """Failure that retrying might fix: connection problems and server errors."""


def _open(url, headers=None, timeout=60, data=None):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    delay = 2
    for attempt in range(ATTEMPTS):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            if error.code < 500 and error.code != 429:
                raise HTTPError(url, error.code, error.reason) from None
            last = f"HTTP {error.code}"
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last = str(getattr(error, "reason", error))
        if attempt < ATTEMPTS - 1:
            time.sleep(delay)
            delay *= 2
    raise NetworkError(f"{url}: {last} after {ATTEMPTS} attempts")


def get_json(url, headers=None):
    with _open(url, headers) as response:
        return json.load(response)


def post_json(url, payload, headers=None):
    """POSTs payload as JSON and returns the JSON reply; for read-only queries, which are safe to retry."""
    body = json.dumps(payload).encode()
    with _open(url, {"Content-Type": "application/json", **(headers or {})}, data=body) as response:
        return json.load(response)


def get_bytes(url, headers=None, limit=None):
    with _open(url, headers) as response:
        data = response.read(limit + 1 if limit else -1)
    if limit and len(data) > limit:
        raise HTTPError(url, "too large", f"over {limit} bytes")
    return data


def download(url, dest, headers=None):
    with _open(url, headers, timeout=300) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)

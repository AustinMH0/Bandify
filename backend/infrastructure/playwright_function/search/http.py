"""Bounded public-page reads; blocked/unknown documents are provider errors."""
from time import monotonic
from urllib.parse import urlparse
import math
import requests
from bs4 import BeautifulSoup

APP_AGENT = 'Groovonomy/1.0 (https://groovonomy.com; https://github.com/AustinMH0/Bandify)'
DESKTOP_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'


def bandcamp_site(url):
    parsed = urlparse(url)
    host = parsed.hostname or ''
    if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port
            or not host.endswith('.bandcamp.com') or host.count('.') != 2
            or host in ('www.bandcamp.com', 'daily.bandcamp.com')):
        raise ValueError('Not an artist Bandcamp site')
    return f'https://{host}'


def page(url, deadline, agent=APP_AGENT, missing_ok=False):
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise TimeoutError('Store lookup deadline exceeded')
    response = requests.get(url, headers={'User-Agent': agent},
                            timeout=(min(1, remaining), min(3, remaining)),
                            allow_redirects=False)
    # Do not follow arbitrary provider/metadata redirects into private endpoints.
    if response.status_code == 404 and missing_ok:
        return None
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError('Unexpected store response')
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.get_text(' ', strip=True).lower() if soup.title else ''
    if any(marker in title for marker in ('client challenge', 'just a moment', 'access denied', 'captcha')):
        raise RuntimeError('Store access challenge')
    return soup


def amount(value):
    if isinstance(value, bool):
        raise ValueError('Invalid store price')
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError('Invalid store price')
    return round(result, 2)

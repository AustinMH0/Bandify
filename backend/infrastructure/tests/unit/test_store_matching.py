"""Offline provider regressions using representative search/purchase markup.

The vayd cover is the observed false positive; remaining rows exercise candidate
ordering and credit/version variants without relying on changing live rankings.
"""
import importlib.util
import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup
import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name('fixtures')
NOT_FOUND = {'price': -1, 'url': ''}


@pytest.fixture(params=['search_results', 'playwright_function'])
def matching(request, monkeypatch):
    path = ROOT / request.param / 'search/matching.py'
    spec = importlib.util.spec_from_file_location('matcher', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('requested, credited, accepted', [
    ('The Weeknd', 'THE WEEKND', True),
    ('Beyoncé', 'Beyonce', True),
    ('JAY-Z', 'Jay Z', True),
    ("Guns N’ Roses", "Guns N Roses", True),
    ('AC/DC', 'ACDC', True),
    ('Earth, Wind & Fire', 'Earth, Wind and Fire', True),
    ('Beyoncé feat. JAY-Z', 'Beyonce & Jay Z', True),
    ('Beyoncé ft. JAY-Z', 'Beyonce featuring Jay Z', True),
    ('The Weeknd', 'Ariana Grande & The Weeknd', True),
    ('Ariana Grande, The Weeknd', 'Ariana Grande feat. The Weeknd', True),
    ('Ariana Grande, The Weeknd', 'Ariana Grande', False),
    ('The Weeknd', 'vayd', False),
    ('The Weeknd', 'The Weeknd Tribute Band', False),
    ('X', 'XX', False),
    ('', 'The Weeknd', False),
    ('The Weeknd', '', False),
    ('The Weeknd', None, False),
    ('Featles', 'les', False),
])
def test_artist_identities(matching, requested, credited, accepted):
    assert matching.artist_matches(requested, credited) is accepted


@pytest.mark.parametrize('requested, candidate, rank', [
    ('Blinding Lights', 'BLINDING LIGHTS', 0),
    ('Déjà Vu', 'Deja Vu', 0),
    ('Blinding Lights', 'Blinding Lights (Original Mix)', 1),
    ('Blinding Lights', 'Blinding Lights - Original Mix', 1),
    ('Blinding Lights', 'Blinding Lights (Cover)', None),
    ('Blinding Lights', 'Blinding Lights (Remix)', None),
    ('Blinding Lights', 'Blinding Lights (Karaoke)', None),
    ('Blinding Lights', 'Blinding Lights (Tribute)', None),
    ('Blinding Lights', 'Blinding Lights (Instrumental)', None),
    ('Blinding Lights (Remix)', 'Blinding Lights (Remix)', 0),
    ('Blinding Lights (Cover)', 'Blinding Lights (Cover)', 0),
    ('Blinding Lights (Karaoke)', 'Blinding Lights (Karaoke)', 0),
    ('Blinding Lights (Tribute)', 'Blinding Lights (Tribute)', 0),
    ('Blinding Lights (Instrumental)', 'Blinding Lights (Instrumental)', 0),
    ('Blinding Lights (Remix)', 'Blinding Lights', None),
    ('Blinding Lights', 'Blinding Light', None),
    ('', '', None),
])
def test_title_versions(matching, requested, candidate, rank):
    assert matching.title_rank(requested, candidate) == rank


def test_lambda_matchers_stay_in_sync():
    assert (ROOT / 'search_results/search/matching.py').read_bytes() == (
        ROOT / 'playwright_function/search/matching.py').read_bytes()


@pytest.fixture()
def stores(monkeypatch):
    modules = {}
    for name in ['search_results', 'playwright_function']:
        package_name = 'real_' + name
        path = ROOT / name / 'search'
        spec = importlib.util.spec_from_file_location(
            package_name, path / '__init__.py', submodule_search_locations=[str(path)])
        package = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, package_name, package)
        spec.loader.exec_module(package)
        modules[name] = package
    return modules


def test_itunes_skips_cover_and_versions_and_prefers_exact(stores, monkeypatch):
    module = sys.modules['real_search_results.itunes_search']
    payload = json.loads((FIXTURES / 'itunes_search.json').read_text())

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    monkeypatch.setattr(module.requests, 'get', lambda *args, **kwargs: Response())
    result = module.ItuneSearch.search_song('The Weeknd', 'Blinding Lights')
    assert result['price'] == 1.29
    assert '/after-hours/' in result['url']
    assert 'geo.itunes.apple.com' in result['url']
    payload['results'] = [payload['results'][0], payload['results'][1], payload['results'][4]]
    assert module.ItuneSearch.search_song('The Weeknd', 'Blinding Lights') == NOT_FOUND
    payload['results'][0].update(artistName='Ariana Grande & The Weeknd')
    assert module.ItuneSearch.search_song('The Weeknd', 'Blinding Lights')['price'] == 0


@pytest.mark.parametrize('provider', ['bandcamp', 'beatport'])
def test_html_providers_choose_exact_among_multiple_rows(stores, monkeypatch, provider):
    module = sys.modules[f'real_playwright_function.{provider}_search']
    search_html = (FIXTURES / f'{provider}_search.html').read_text()
    pages = []

    def page_html(url, deadline):
        pages.append(url)
        if '/search?' in url:
            return search_html
        return (FIXTURES / 'bandcamp_track.html').read_text()

    monkeypatch.setattr(module, 'page_html', page_html)
    cls = module.BandcampSearch if provider == 'bandcamp' else module.BeatportSearch
    result = cls().search_song('Blinding Lights', 'The Weeknd')
    assert result['price'] == (1.29 if provider == 'bandcamp' else 1.49)
    assert result['url'].endswith('/blinding-lights' if provider == 'bandcamp' else '/blinding-lights/103')
    if provider == 'bandcamp':
        assert len(pages) == 2
        assert not any('vayd.' in url for url in pages)

    # Cover, tribute and wrong-version rows must yield N/A without a purchase visit.
    soup = BeautifulSoup(search_html, 'html.parser')
    rows = soup.select('li.searchresult' if provider == 'bandcamp' else 'div[class*="TableRow"]')
    search_html = ''.join(str(row) for row in rows[:2])
    pages.clear()
    assert cls().search_song('Blinding Lights', 'The Weeknd') == NOT_FOUND
    assert len(pages) == 1


@pytest.mark.parametrize('change', ['artist', 'title', 'missing'])
def test_bandcamp_purchase_page_must_confirm_identity(stores, monkeypatch, change):
    module = sys.modules['real_playwright_function.bandcamp_search']
    track_html = (FIXTURES / 'bandcamp_track.html').read_text()
    if change == 'artist':
        track_html = track_html.replace('The Weeknd', 'vayd')
    elif change == 'title':
        track_html = track_html.replace('Blinding Lights', 'Blinding Lights (Cover)')
    else:
        track_html = '<span>name your price</span>'
    monkeypatch.setattr(module, 'page_html', lambda url, deadline: (
        (FIXTURES / 'bandcamp_search.html').read_text() if '/search?' in url else track_html))
    assert module.BandcampSearch().search_song('Blinding Lights', 'The Weeknd') == NOT_FOUND


def test_bandcamp_verified_name_your_price_is_zero(stores, monkeypatch):
    module = sys.modules['real_playwright_function.bandcamp_search']
    track_html = (FIXTURES / 'bandcamp_track.html').read_text().replace('$1.29', 'name your price')
    monkeypatch.setattr(module, 'page_html', lambda url, deadline: (
        (FIXTURES / 'bandcamp_search.html').read_text() if '/search?' in url else track_html))
    assert module.BandcampSearch().search_song('Blinding Lights', 'The Weeknd')['price'] == 0

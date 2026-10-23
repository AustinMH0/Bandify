"""Real response fragments captured on 2026-10-23; all replay is offline."""
import json
import sys
from pathlib import Path
from time import monotonic
from bs4 import BeautifulSoup
import pytest
from .test_store_matching import stores

FIXTURES = Path(__file__).with_name('fixtures')


def replay(monkeypatch, stores, provider, pages):
    module = sys.modules[f'real_playwright_function.{provider}_search']
    calls = []
    def read(url, *args, **kwargs):
        calls.append(url)
        return BeautifulSoup(pages.pop(0), 'html.parser') if pages and pages[0] is not None else None
    monkeypatch.setattr(module, 'page', read)
    return module, calls


@pytest.mark.parametrize('track,artist', [('Glue','Bicep'),('Kerala','Bonobo')])
def test_beatport_real_embedded_prices(stores, monkeypatch, track, artist):
    module, calls = replay(monkeypatch, stores, 'beatport', [(FIXTURES/f'beatport_{track.lower()}_http.html').read_text()])
    result = module.BeatportSearch().search_song(track, artist)
    assert result['price'] == 1.49
    assert result['matched_artist'] == artist
    assert result['matched_title'] == track + ' (Original Mix)'
    assert '/track/' in result['url']
    assert len(calls) == 1


@pytest.mark.parametrize('change', ['artist','mix','currency','nan','negative','schema','missing_mix'])
def test_beatport_never_guesses_identity_or_price(stores, monkeypatch, change):
    soup = BeautifulSoup((FIXTURES/'beatport_glue_http.html').read_text(), 'html.parser')
    data = json.loads(soup.script.string)
    rows = data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['tracks']['data']
    for row in rows:
        if change == 'artist': row['artists'][0]['artist_name'] = 'Bicep Tribute Band'
        if change == 'mix': row['mix_name'] = 'Someone Remix'
        if change == 'currency': row['price']['code'] = 'EUR'
        if change == 'nan': row['price']['value'] = 'NaN'
        if change == 'negative': row['price']['value'] = -1
        if change == 'missing_mix': row.pop('mix_name')
    if change == 'schema': data = {}
    soup.script.string = json.dumps(data)
    module, _ = replay(monkeypatch, stores, 'beatport', [str(soup)])
    if change in ('artist','mix'):
        assert module.BeatportSearch().search_song('Glue','Bicep')['price'] == -1
    else:
        with pytest.raises((RuntimeError, ValueError, KeyError)):
            module.BeatportSearch().search_song('Glue','Bicep')


def test_bandcamp_reads_digital_offer_without_search_or_browser(stores, monkeypatch):
    pages = [(FIXTURES/name).read_text() for name in ['bandcamp_music_http.html','bandcamp_glue_http.html']]
    module, calls = replay(monkeypatch, stores, 'bandcamp', pages)
    result = module.BandcampSearch(['https://bicep.bandcamp.com']).search_song('Glue','Bicep')
    assert result['price'] == 1.30  # not set_price=1.5 or a CD/vinyl offer
    assert result['matched_artist'] == 'Bicep'
    assert calls == ['https://bicep.bandcamp.com/music','https://bicep.bandcamp.com/track/glue']


def test_bandcamp_missing_artist_returns_search_link_without_fetch(stores, monkeypatch):
    module, calls = replay(monkeypatch, stores, 'bandcamp', [])
    result = module.BandcampSearch().search_song('Glue','Bicep')
    assert result['price'] == -1
    assert result['url'] == 'https://bandcamp.com/search?q=Glue%20Bicep&item_type=t'
    assert not calls


@pytest.mark.parametrize('change', ['artist','title','physical_only','unknown','free'])
def test_bandcamp_identity_and_digital_offer(stores, monkeypatch, change):
    soup = BeautifulSoup((FIXTURES/'bandcamp_glue_http.html').read_text(), 'html.parser')
    data = json.loads(soup.select_one('[data-tralbum]')['data-tralbum'])
    if change == 'artist': data['artist'] = 'Bicep Tribute Band'
    if change == 'title': data['current']['title'] = 'Glue (Remix)'
    soup.select_one('[data-tralbum]')['data-tralbum'] = json.dumps(data)
    if change == 'physical_only':
        soup = BeautifulSoup(str(soup).replace('DigitalFormat','CDFormat'),'html.parser')
    if change == 'unknown': soup = BeautifulSoup('<p>Loading...</p>','html.parser')
    if change == 'free':
        node = soup.select_one('script[type="application/ld+json"]')
        data = json.loads(node.string)
        data['inAlbum']['albumRelease'][0]['offers']['price'] = 0
        node.string = json.dumps(data)
    module = sys.modules['real_playwright_function.bandcamp_search']
    if change in ('physical_only','unknown'):
        with pytest.raises(RuntimeError): module.BandcampSearch.track_result(soup,'https://bicep.bandcamp.com/track/glue','Glue','Bicep')
    else:
        result = module.BandcampSearch.track_result(soup,'https://bicep.bandcamp.com/track/glue','Glue','Bicep')
        assert result is None if change in ('artist','title') else result['price'] == 0


@pytest.mark.parametrize('status,fixture', [(200,'bandcamp_challenge.html'),(403,'beatport_challenge.html')])
def test_challenges_are_errors(stores, monkeypatch, status, fixture):
    import requests
    module = sys.modules['real_playwright_function.http']
    class Response:
        status_code = status
        text = (FIXTURES/fixture).read_text()
        def raise_for_status(self):
            if status >= 400: raise requests.HTTPError('403')
    monkeypatch.setattr(module.requests, 'get', lambda *args, **kwargs: Response())
    with pytest.raises((RuntimeError, requests.HTTPError)):
        module.page('https://bandcamp.com/example',monotonic()+9)


@pytest.mark.parametrize('url', ['https://evil.example/','https://bandcamp.com/','http://bicep.bandcamp.com/','https://bicep.bandcamp.com.evil.test/','https://u:p@bicep.bandcamp.com/','https://bicep.bandcamp.com:443/'])
def test_bandcamp_metadata_cannot_target_arbitrary_hosts(stores,url):
    module=sys.modules['real_playwright_function.http']
    with pytest.raises(ValueError): module.bandcamp_site(url)

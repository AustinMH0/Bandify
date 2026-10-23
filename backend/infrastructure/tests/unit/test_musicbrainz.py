import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from sqlalchemy import create_engine, text
from admission import Busy, musicbrainz_slot, itunes_slot
import musicbrainz

FIXTURES = Path(__file__).with_name('fixtures')


def test_real_artist_relation_with_request_spacing(tmp_path, monkeypatch):
    calls=[]
    def get(url,params):
        calls.append((url,params))
        name='search' if len(calls)==1 else 'artist'
        return json.loads((FIXTURES/f'musicbrainz_{name}.json').read_text())
    delays=[]
    monkeypatch.setattr(musicbrainz,'_get',get)
    monkeypatch.setattr(musicbrainz,'sleep',delays.append)
    engine=create_engine(f"sqlite:///{tmp_path/'gate.db'}")
    assert musicbrainz.discover_bandcamp_sites('Bicep',engine)==['https://bicep.bandcamp.com']
    assert len(calls)==2 and calls[1][1]=={'inc':'url-rels'}
    assert delays==[1.1]
    with pytest.raises(Busy): musicbrainz.discover_bandcamp_sites('Bicep',engine)
    assert len(calls)==2


@pytest.mark.parametrize('artists',[[],[{'name':'Bicep Tribute'}],[{'name':'Bicep'},{'name':'Bicep'}]])
def test_ambiguous_or_missing_artist_never_guesses(tmp_path,monkeypatch,artists):
    monkeypatch.setattr(musicbrainz,'_get',lambda *args:{'artists':artists})
    assert musicbrainz.discover_bandcamp_sites('Bicep',create_engine(f"sqlite:///{tmp_path/'gate.db'}"))==[]


def test_musicbrainz_gate_is_shared_and_independent_of_apple(tmp_path):
    url=f"sqlite:///{tmp_path/'gate.db'}"
    entered,release=Event(),Event()
    def active():
        with musicbrainz_slot(create_engine(url)):
            entered.set(); assert release.wait(5)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future=pool.submit(active); assert entered.wait(5)
        try:
            with itunes_slot(create_engine(url)): pass
            with pytest.raises(Busy):
                with musicbrainz_slot(create_engine(url)): pytest.fail('Overlapping discovery')
        finally: release.set()
        future.result()
    with pytest.raises(Busy):
        with musicbrainz_slot(create_engine(url)): pytest.fail('Handoff needs a full second')


def test_musicbrainz_errors_release_lease_and_keep_spacing(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path/'gate.db'}")
    with pytest.raises(RuntimeError):
        with musicbrainz_slot(engine): raise RuntimeError('provider failed')
    with engine.connect() as connection:
        row=connection.execute(text('SELECT owner, lease_until, next_allowed FROM musicbrainz_search_admission')).one()
        assert row.owner is None and row.lease_until==0 and row.next_allowed>0


def test_musicbrainz_uses_descriptive_agent_and_does_not_retry(monkeypatch):
    calls=[]
    class Response:
        status_code=503
        def raise_for_status(self):
            import requests
            raise requests.HTTPError('503')
    def get(*args,**kwargs): calls.append((args,kwargs));return Response()
    monkeypatch.setattr(musicbrainz.requests,'get',get)
    import requests
    with pytest.raises(requests.HTTPError): musicbrainz._get(musicbrainz.BASE,{'query':'artist:"Bicep"'})
    assert len(calls)==1
    kwargs=calls[0][1]
    assert kwargs['headers']['User-Agent'].startswith('Groovonomy/1.0 (https://groovonomy.com')
    assert '@' not in kwargs['headers']['User-Agent']
    assert kwargs['allow_redirects'] is False and kwargs['params']['fmt']=='json'

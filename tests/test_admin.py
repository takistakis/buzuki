from flask import url_for

from buzuki.songs import Song
from tests.factories import SongFactory


class TestLogin:
    def test_session(self, client):
        with client.session_transaction() as session:
            session['logged_in'] = True
        resp = client.get(url_for('admin.index'))
        assert resp.status_code == 200

    def test_form(self, client):
        resp = client.post(
            url_for('admin.login'),
            data={'password': 'admin'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with client.session_transaction() as session:
            assert session['logged_in']
        resp = client.get(url_for('admin.login'), follow_redirects=True)
        assert 'Έχεις ήδη συνδεθεί'.encode() in resp.data

    def test_redirect_and_login(self, client):
        url = url_for('admin.add')
        login_url = url_for('admin.login')

        resp = client.get(url)
        assert resp.status_code == 302
        assert resp.location == '/admin/login/?next=/admin/add/'

        resp = client.get(url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Συνδέσου για να συνεχίσεις'.encode() in resp.data
        assert (
            b'<input id="next" name="next" type="hidden" value="/admin/add/">'
        ) in resp.data

        data = {
            'password': 'admin',
            'next': '/admin/add/',
        }

        resp = client.post(login_url, data=data)
        assert resp.status_code == 302
        assert resp.location == '/admin/add/'

        resp = client.get('/admin/add/')
        assert resp.status_code == 200
        assert 'Νέο τραγούδι'.encode() in resp.data

    def test_wrong_password(self, client):
        resp = client.post(
            url_for('admin.login'),
            data={'password': 'wrong password'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert 'Λάθος κωδικός'.encode() in resp.data


def test_logout(client):
    with client.session_transaction() as session:
        session['logged_in'] = True
    client.get(url_for('admin.logout'), follow_redirects=True)
    with client.session_transaction() as session:
        assert not session['logged_in']


def test_add(client):
    with client.session_transaction() as session:
        session['logged_in'] = True
    resp = client.get(url_for('admin.add'))
    assert 'Νέο τραγούδι'.encode() in resp.data
    resp = client.post(
        url_for('admin.add'),
        data={
            'name': 'name',
            'artist': 'artist',
            'scale': 'scale',
            'rhythm': 'rhythm',
            'body': 'body',
            'link': 'https://www.youtube.com/watch?v=asdfasdf',
        },
        follow_redirects=True
    )
    song = Song.get('name')
    assert song.name == 'name'


def test_save_delete(client):
    with client.session_transaction() as session:
        session['logged_in'] = True
    song = SongFactory(body='Bm F# Bm')
    song.tofile()
    assert len(Song.all()) == 1
    url = url_for('admin.save', slug='name', semitones=1)
    resp = client.get(url, follow_redirects=True)
    assert resp.status_code == 200
    song = Song.get('name')
    assert song.body == 'Cm G  Cm'
    resp = client.get(url_for('admin.delete', slug='name'),
                      follow_redirects=True)
    assert Song.all() == []
    resp = client.get(url_for('admin.delete', slug='name'),
                      follow_redirects=True)
    assert 'Δεν υπάρχει τέτοια σελίδα'.encode() in resp.data

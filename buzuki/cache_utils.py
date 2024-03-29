"""Cache utilities for buzuki.

The disc is accessed only for song detail view, and only if the song is not
already in OS cache.

There are two caches, song and artist, both of type Dict[str, Dict].

See test_cache.py for examples.
"""

import logging
from pathlib import Path

import yaml
from flask import current_app as app

from buzuki import cache
from buzuki.utils import greeklish, unaccented


def _sorted_dict(data: dict, last_name: bool = False) -> dict:
    def key_func(item):
        name = item[1]['name']
        if last_name:
            name = name.split()[-1]

        return unaccented(name)

    return dict(sorted(data.items(), key=key_func))


def clear():
    cache.clear()


def get_songs():
    songs = cache.get('songs')
    if not songs:
        songs, _ = fill_cache()
    return songs


def get_artists():
    artists = cache.get('artists')
    if not artists:
        _, artists = fill_cache()
    return artists


def get_related(slug):
    related = cache.get('related')
    if not related:
        fill_related_cache()
    return cache.get(f'related:{slug}')


def fill_cache():
    logging.info("Filling song/artist cache...")

    songs = {}
    artists = {}

    directory: Path = app.config['DIR'] / 'songs'
    path: Path
    for path in directory.iterdir():
        with path.open() as f:
            name = f.readline().strip().split(' (')[0]
            slug = greeklish(name)
            artist = f.readline().strip()
            artist_slug = greeklish(artist)
            f.readline()  # Link
            f.readline()  # Empty line
            scale_lines = []
            line = f.readline()
            while line != '\n':
                scale_lines.append(line)
                line = f.readline()
            scale = ''.join(scale_lines).strip()

            songs[slug] = {
                'name': name,
                'artist': artist,
                'artist_slug': artist_slug,
                'scale': scale,
            }

            if artist_slug not in artists:
                artists[artist_slug] = {
                    'name': artist,
                    'songs': [],
                }
            artists[artist_slug]['songs'].append({
                'name': name,
                'slug': greeklish(name),
            })

    # Sort songs by song name
    songs = _sorted_dict(songs)

    # Sort artists by artist last name
    artists = _sorted_dict(artists, last_name=True)

    # Sort songs of each artist
    for value in artists.values():
        value['songs'].sort(key=lambda song: unaccented(song['name']))

    cache.set('songs', songs)
    cache.set('artists', artists)

    logging.info("Filled song/artist cache")

    return songs, artists


def fill_related_cache():
    logging.info("Filling related cache...")

    path: Path = app.config['DIR'] / 'related.yml'
    try:
        all_related = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        all_related = {}
    for slug, related in all_related.items():
        cache.set(f'related:{slug}', related)
    cache.set('related', True)

    logging.info("Filled related cache")

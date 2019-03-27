"""
Test vid.py
"""
import glob
import os
import shutil

import podgen
import pytest

import vid

PLAYLIST = "https://www.youtube.com/playlist?list=PLuGFF6RJgaMrlxVxEB7XsBerrIFgnqZIa"
OGN_REASON = 'Skipped because it is very long. To enable set ALL_TESTS=True'
LONG_TEST = pytest.mark.skipif(not os.environ.get('ALL_TESTS'), reason=OGN_REASON)
LONG_TEXT = """Check out our store for official Critical Role merch: https://goo.gl/BhXLst


Catch Critical Role live Thursdays at 7PM PT on Alpha and Twitch:
Alpha: https://goo.gl/c4ZsBj
Twitch: https://goo.gl/D9fsrS

Listen to the Critical Role podcast: https://goo.gl/jVwPBr

Check out the Geek and Sundry Twitch stream for more, with Critical Role on Thursdays from 7-10pm on http://www.twitch.tv/geekandsundry

Our story begins as Vox Machina, the heroes of Emon, arrive at the cavernous underground city of Kraghammer. After wiping out a grave threat to Emon’s emperor, Sovereign Uriel Tal'Dorei III, the band of adventurers has been sent on a journey by Arcanist, Allura Vysoren to find Lady Kima of Vord, a Halfling Paladin of Bahamut, who was drawn to Kraghammer upon learning of a great evil resting beneath it. The party get their bearings in the sprawling, dwarven city, meet a few of its more colorful denizens, and learn that the dwarves have been dealing with unnatural creatures spilling out of the mines in recent months. The mine’s overseer, Nostoc Greyspine, barely finishes explaining their troubles, when a pack of goblins and ogres come spilling out of the mine’s entrance, pursued by something far worse.

Concept Artwork for 'The Silver Legacy’ movie created by Jessica Mae Stover (jessicastover.com) and Greg Martin (artofgregmartin.com)."""


def test_read_json_info():
    fname = glob.glob('tests/media/Critical Role _ Campaign 1/*.info.json')[0]

    assert 'uploader' in vid.read_json_info(fname)


def test_create_episodes():
    fnames = glob.glob('tests/media/Critical Role _ Campaign 1/*.info.json')
    eps = vid.create_episodes(fnames, 'critical', vid.FORMATS['medium'])

    assert len(eps) == 140
    assert isinstance(eps[0], podgen.Episode)


def test_parse_date_string():
    date_str = "20190522"
    date = vid.parse_date_string(date_str, -8)

    assert str(date) == "2019-05-22 00:00:00-08:00"


def test_shorten_to_len():
    expect = """Check out our store for official Critical Role merch: https://goo.gl/BhXLst


Catch Critical Role live Thursdays at 7PM PT on Alpha and Twitch:
Alpha: https://goo.gl/c4ZsBj
Twitch: https://goo.gl/D9fsrS

Listen to the Critical Role podcast: https://goo.gl/jVwPBr"""

    assert vid.shorten_to_len(LONG_TEXT, 250) == expect


def test_shorten_to_len_short_input():
    expect = """Check out our store for official Critical Role merch: https://goo.gl/BhXLst"""

    line = LONG_TEXT[:].split('\n')[0]
    assert vid.shorten_to_len(line, 250) == expect


@LONG_TEST
def test_fetch_playlist_info():
    try:
        cur = os.getcwd()
        os.chdir('/tmp')
        folder = 'beingelse'
        vid.fetch_playlist_info(PLAYLIST, folder)
        assert glob.glob('media/{}/*'.format(folder))
    finally:
        shutil.rmtree('media')
        os.chdir(cur)


def test_prune_playlist_info():
    try:
        cur = os.getcwd()
        os.chdir('/tmp')
        folder = 'beingelse'

        src = os.path.join(cur, 'tests', 'media', folder)
        dst = os.path.join('/tmp/media/beingelse')
        shutil.copytree(src, dst)

        fnames = sorted(glob.glob('media/{}/*'.format(folder)))
        vid.prune_playlist_info(fnames)
        info = vid.read_json_info(fnames[0])
        assert 'uploader' in info
        assert 'chapters' not in info
    finally:
        shutil.rmtree('media')
        os.chdir(cur)


def test_fetch_video():
    try:
        url = "https://www.youtube.com/watch?v=1qCqP_K1fVI"
        vid.fetch_video(url, vid.FORMATS['audio'])
        fnames = glob.glob('media/6 Weird*')
        assert len(fnames) == 1
    finally:
        for fname in glob.glob('media/6 Weird*'):
            print(fname)
            os.remove(fname)

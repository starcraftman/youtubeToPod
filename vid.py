"""
Script to convert & create the podgen RSS to be served.
"""
import datetime
import glob
import json
import os
import sys

import podgen
import youtube_dl

SUMMARY_LEN = 250
CROLE_URL = "https://www.youtube.com/playlist?list=PL7atuZxmT954bCkC062rKwXTvJtcqFB8i"
FORMATS = {
    "audio": "140",
    "medium": "18",
    "high": "22",
}


def youtube_download(url, opts_update=None, playlist=None):
    """
    Fetch a video from a youtube url with youtube_dl.

    Use opts_update to override the default options.

    Default
    ydl_opts = {
        "format": "140",
        "ignoreerrors": True,
        "outtmpl": "media/%(playlist)s/%(playlist_index)s - %(title)s.mp4",
        "writeinfojson": True,
    }

    Important Options:
    ydl_opts = {
        "ratelimit": 3000000,
        "playlist_items": "1",
        "logger": YDLLogger(),
        "progress_hooks": [ydl_hook],
    }
    """
    output_template = "media/%(title)s.mp4"
    if playlist:
        output_template = "media/{}/%(playlist_index)s - %(title)s.mp4".format(playlist)

    ydl_opts = {
        "format": "140",
        "ignoreerrors": True,
        "outtmpl": output_template,
    }

    if opts_update:
        ydl_opts.update(opts_update)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def fetch_playlist_info(url, folder, format_id=FORMATS["medium"]):
    opts_update = {
        "format": format_id,
        "skip_download": True,
        "writeinfojson": True,
    }
    youtube_download(url, opts_update=opts_update, playlist=folder)


def fetch_video(url, format_id):
    """
    Args:
        url - Playlist from youtube.
        format_id - A format id supported by the video.
        playlist_items - Series of indexes of playlist to download. A string CSV of integers.
    """
    opts_update = {
        "format": format_id,
    }
    youtube_download(url, opts_update=opts_update)


def parse_info(fname):
    """
    Parse info from the video information file.
    Preserve only the useful information to avoid overload when printing.

    Returns: Dictionary containing information on podcast episode.
    """
    with open(fname) as fin:
        info = json.load(fin)

    keep_keys = ["id", "upload_date", "title", "uploader", "thumbnail",
                 "description", "duration", "webpage_url", "formats", "format_id",
                 "playlist", "playlist_index", "filesize", "format", "fulltitle"]
    for key in set(info.keys()) - set(keep_keys):
        del info[key]

    return info


def parse_date_string(date_str, timezone_offset=0):
    """
    Take a string of form yyyymmdd and an offset from UTC and
    return a datetime.datetime object representing that time.
    """
    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:])

    return datetime.datetime(year=year, month=month, day=day,
                             tzinfo=datetime.timezone(datetime.timedelta(hours=timezone_offset)))


def shorten_to_len(text, max_len):
    """
    Take a text of arbitrary length and split on new lines.
    Keep adding whole lines until max_len is reached or surpassed.

    Returns the new shorter text.
    """
    text_parts = text.split("\n")
    shorter_text = ''

    while len(shorter_text) < max_len:
        shorter_text += text_parts[0] + "\n"
        text_parts = text_parts[1:]

    return shorter_text.rstrip()


def parse_episodes(folder, series_name, format_id):
    episodes = []
    fnames = sorted(glob.glob(folder + '/*'))

    for fname in fnames:
        info = parse_info(fname)
        fmt_info = [x for x in info["formats"] if x['format_id'] == format_id][0]

        media = podgen.Media(
            url="http://starcraftman.com/video/{}/{}.mp4".format(series_name, info["playlist_index"]),
            duration=datetime.timedelta(seconds=int(info["duration"])),
            size=fmt_info["filesize"],
            type="video/mp4",
        )
        episode = podgen.Episode(
            title=info["title"],
            position=info['playlist_index'],
            image=info["thumbnail"],
            summary=shorten_to_len(info["description"], SUMMARY_LEN),
            long_summary=info["description"],
            publication_date=parse_date_string(info["upload_date"]),
            media=media,
        )
        episodes.append(episode)

    return episodes


def create_podcast(episodes, series_name):
    episode = episodes[0]
    pod = podgen.Podcast(name=episode.title, description=episode.long_summary,
                         website="http://starcraftman.com/rss/{}.rss".format(series_name),
                         explicit=False, image=episode.image, language="EN")
    pod.episodes += episodes

    return pod


def main():
    if len(sys.argv) != 4 or sys.argv[-1] not in FORMATS.keys():
        print("Usage: {} youtube_playlist series_name format_id".format(sys.argv[0]))
        print("\n    Select format_id from [{}]".format(", ".join(FORMATS.keys())))
        sys.exit(1)

    url, series_name, format_key = sys.argv[1:]
    try:
        os.mkdir("rss")
    except OSError:
        pass

    fetch_playlist_info(url, series_name)
    episodes = parse_episodes("media/{}/".format(series_name), series_name, FORMATS[format_key])
    pod = create_podcast(episodes, series_name)

    fname = 'rss/{}.rss'.format(series_name)
    pod.rss_file(fname)
    print('RSS file written to: ' + fname)


if __name__ == "__main__":
    main()

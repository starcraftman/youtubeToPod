"""
Script to convert & create the podgen RSS to be served.
"""
import argparse
import datetime
import glob
import json
import os
import sys

import podgen
import youtube_dl

SUMMARY_LEN = 250
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
    output_template = "web/media/%(id)s.mp4"
    if playlist:
        output_template = "web/media/{}/%(playlist_index)s - %(title)s.mp4".format(playlist)

    ydl_opts = {
        "format": "140",
        "ignoreerrors": True,
        "outtmpl": output_template,
    }

    if opts_update:
        ydl_opts.update(opts_update)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


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


def fetch_playlist_info(url, folder, format_id=FORMATS["medium"]):
    opts_update = {
        "format": format_id,
        "skip_download": True,
        "writeinfojson": True,
    }
    youtube_download(url, opts_update=opts_update, playlist=folder)


def read_json_info(fname):
    """
    Parse info from the video information file.

    Returns: Dictionary containing information on podcast episode.
    """
    with open(fname) as fin:
        return json.load(fin)


def prune_playlist_info(fnames):
    """
    Prune the playlist metadata to ONLY the required information.
    """
    for fname in fnames:
        info = read_json_info(fname)

        keep_keys = ["id", "upload_date", "title", "uploader", "thumbnail",
                     "description", "duration", "webpage_url", "formats", "format_id",
                     "playlist", "playlist_index", "filesize", "format", "fulltitle"]
        for key in set(info.keys()) - set(keep_keys):
            del info[key]

        for fmt_val in info["formats"][:]:
            if fmt_val["format_id"] not in FORMATS.values():
                info["formats"].remove(fmt_val)

        with open(fname, 'w') as fout:
            json.dump(info, fout, separators=(',', ':'))


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
    shorter_text = ''
    text_parts = text.split("\n")

    while text_parts and len(shorter_text) < max_len:
        shorter_text += text_parts[0] + "\n"
        text_parts = text_parts[1:]

    return shorter_text.rstrip()


def create_episodes(fnames, series_name, format_id):
    episodes = []

    for fname in fnames:
        info = read_json_info(fname)
        fmt_info = [x for x in info["formats"] if x['format_id'] == format_id][0]

        media = podgen.Media(
            url="http://starcraftman.com/video/{}/{}.mp4".format(series_name, info["playlist_index"]),
            duration=datetime.timedelta(seconds=int(info["duration"])),
            size=fmt_info["filesize"],
            type="video/mp4",
        )
        episode = podgen.Episode(
            title=info["title"],
            image=info["thumbnail"],
            summary=shorten_to_len(info["description"], SUMMARY_LEN),
            long_summary=info["description"],
            publication_date=parse_date_string(info["upload_date"]),
            media=media,
        )
        episodes.append(episode)

    return episodes


def create_podcast(episodes, series_name, title=None, description=None, persons=None):
    """
    Create a podcast based on the episodes & required information.
    """
    episode = episodes[0]
    if not title:
        title = episode.title
    if not description:
        description = episode.summary

    pod = podgen.Podcast(name=title, description=description,
                         website="http://starcraftman.com/rss/{}.rss".format(series_name),
                         explicit=True, image=episode.image, language="EN")
    pod.episodes += episodes

    if persons:
        pod.authors = persons
        pod.owner = persons[0]

    return pod


def create_parser():
    """
    Generate a simple command line parser.
    """
    prog = 'python ./' + sys.argv[0]
    desc = """Generate a RSS feed based on a youtube playlist.

{prog} URL series_name format_id
        Generate an RSS feed for URL, store metadata in series_name for retrieval.
        Select audio, medium or high for format_id.
{prog} URL series_name format_id --title A title --description A description for podcast
        Same as above, manually override the title and description of the podcast.
    """.format(prog=prog)

    parser = argparse.ArgumentParser(prog=prog, description=desc,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('url', help='The youtube playlist.')
    parser.add_argument('series_name', help='The short name of the series (storage).')
    parser.add_argument('format', choices=FORMATS.keys(), help='The format to fetch.')
    parser.add_argument('-t', '--title', nargs='+', default=None, help='The title of the podcast.')
    parser.add_argument('-d', '--description', nargs='+', default=None, help='The short description of podcast.')

    return parser


def main():
    args = create_parser().parse_args()
    if args.title:
        args.title = " ".join(args.title)
    if args.description:
        args.description = " ".join(args.description)

    try:
        os.mkdir("web/rss")
    except OSError:
        pass

    fetch_playlist_info(args.url, args.series_name)

    info_files = sorted(glob.glob("web/media/{}/*.info.json*".format(args.series_name)))
    prune_playlist_info(info_files)
    episodes = create_episodes(info_files, args.series_name, FORMATS[args.format])

    info = read_json_info(info_files[0])
    persons = [podgen.Person(info['uploader'], 'N/A')]
    pod = create_podcast(episodes, args.series_name, title=args.title,
                         description=args.description, persons=persons)

    fname = 'web/rss/{}.rss'.format(args.series_name)
    pod.rss_file(fname)
    print('RSS file written to: ' + fname)


if __name__ == "__main__":
    main()

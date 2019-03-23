"""
Sanic webserver to serve the podcasts on demand.
"""
import glob
import os

import sanic
import sanic.response

import vid

app = sanic.Sanic()
app.config.RESPONSE_TIMEOUT = 600  # Downloading takes long


@app.route("/rss/<series>.rss")
async def get_rss(request, series):
    return await sanic.response.file('rss/{}.rss'.format(series))


@app.route("/video/<series>/<episode>.mp4")
async def get_video(request, series, episode):
    episode = int(episode) - 1
    fname = sorted(glob.glob("media/{}/*.info.json".format(series)))[episode]
    info = vid.parse_info(fname)
    vid.fetch_video(info["webpage_url"], info["format_id"])

    vids = glob.glob("media/*.mp4")
    vid_part = info["title"][:10]
    if len(vids) > 1:
        for video in vids[:]:
            if vid_part not in video:
                os.remove(video)
                vids.remove(video)

    return await sanic.response.file_stream(vids[0])


def main():
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

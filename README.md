# Youtube To RSS Feed

Convert an existing youtube playlist into a RSS feed that can be added to a podcast client.
To this end, the first step is to analyze all the videos in the playlist and store metadata locally.
The second step is to add the routes in web.py to an existing flask/sanic install. This allows you to
on the fly download & stream to a user the requested video.

Depends on:

- podgen
- youtube_dl
- sanic (or flask, or really any server)

## Usage

1. Install dependencies with: ```python setup.py deps```
1. Ensure that routes in `web.py` inserted into a working flask/sanic install.
1. Generate the required RSS feed with `vid.py`, see usage from --help.
   You can generate an audio only feed, medium quality video or high quality video.
1. Add the generated podcast to your podcast client.
1. Enjoy the series.

## Disclaimer

This is a proof of concept, you use it at your own liability. I am not a lawyer, I just made a thing
and am sharing it. You in essence are reehostng the video and streaming it to clients from a server. This may
or may not be ok depeonding on the license of the content or regional copyright laws.

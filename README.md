# genRss

Convert an existing youtube playlist into a subscribable playlist. Then on demand generate
the youtube_dl conversion of the podcast and serve it to download.
Should not store file beyond conversion/serve.

Depends on:

- podgen
- youtube_dl
- sanic (serves stuff)


## Usage

First, generate the RSS feed based on playlist link with vid.py.
Then, you should be able to retrieve them from the server at `video/series/1.mp4`
I need to test in a podcast client still.


## Setup

```python setup.py deps```

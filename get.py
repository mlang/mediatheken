#!/usr/bin/env python3
"""Parse XZ compressed JSON and produce HTML."""
from collections import defaultdict
from lzma import LZMADecompressor
from json import loads
from os.path import dirname
from re import sub, MULTILINE

from jinja2 import Environment, FileSystemLoader
from requests import get

def main():
    """Get mediathek-Data and write HTML files."""
    response = get('http://m1.picn.de/f/Filmliste-akt.xz')
    response.raise_for_status()
    text = LZMADecompressor().decompress(response.content).decode('UTF-8')
    # Change from dictionary with multiple identical keys to array
    text = sub(r'^  "Filmliste" :', "", text, flags=MULTILINE)
    text = sub(r'^  "X" :', "", text, flags=MULTILINE)
    text = '[' + text[1:-2] + ']'
    json = loads(text)
    text = None
    # Remove header
    json.pop(0)
    json.pop(0)

    channel = None
    channels = defaultdict(list)
    for row in json:
        if len(row[0]) > 0:
            channel = row[0]
        channels[channel].append({
            'name': row[2],
            'date': row[3],
            'time': row[4],
            'url': row[8]
        })
    json = None

    # Sort
    for movies in channels.values():
        def yyyymmddhhmm(k):
            """Concatenate date, time and title."""
            date = k['date']
            if len(date) == 10:
                return date[6:]+date[3:5]+date[0:2]+k['time']+k['name']
            else:
                return '0000000000:00:00'+k['name']
        movies.sort(key=yyyymmddhhmm, reverse=True)

    env = Environment(loader=FileSystemLoader(dirname(__file__)))
    def render(file, template, **kwargs):
        """A helper function for rendering templates to a file."""
        print(env.get_template(template).render(kwargs), file=file)
    for channel, movies in channels.items():
        with open("%s.html" % channel, "w") as html:
            render(html, 'channel.tmpl', name=channel, movies=movies)
    with open('index.html', 'w') as html:
        render(html, 'index.tmpl', channels=sorted(channels.keys()))

if __name__ == '__main__':
    main()

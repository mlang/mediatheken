#!/usr/bin/env python3
"""Parse XZ compressed JSON and produce HTML."""
from collections import defaultdict
from lzma import LZMADecompressor
from json import loads
from os.path import dirname
from re import sub, MULTILINE

from jinja2 import Environment, FileSystemLoader
from requests import get

def fetch():
    """Get the data and return a dictionary of channels to a list of movies."""
    response = get('http://m1.picn.de/f/Filmliste-akt.xz')
    response.raise_for_status()
    data = LZMADecompressor().decompress(response.content).decode('UTF-8')
    # Change from dictionary with multiple identical keys to array
    data = sub(r'"Filmliste":', "", data, flags=MULTILINE)
    data = sub(r',"X":', ",", data, flags=MULTILINE)
    data = '[' + data[1:-1] + ']'
    data = loads(data)
    # Remove header
    data = data[2:]

    sender = None
    result = defaultdict(list)
    for row in data:
        if len(row[0]) > 0:
            sender = row[0]
        result[sender].append({
            'name': row[2],
            'date': row[3],
            'time': row[4],
            'url': row[8]
        })
    data = None
    sender = None
    for movies in result.values():
        def yyyymmddhhmm(k):
            """Concatenate date, time and title."""
            date = k['date']
            if len(date) == 10:
                return date[6:]+date[3:5]+date[0:2]+k['time']+k['name']
            else:
                return '0000000000:00:00'+k['name']
        movies.sort(key=yyyymmddhhmm, reverse=True)
    return result

###############################################################################

def main():
    """Fetch JSON and write HTML."""
    env = Environment(loader=FileSystemLoader(dirname(__file__)))
    def render(file, template, **kwargs):
        """A helper function for rendering templates to a file."""
        str = env.get_template(template).render(kwargs)
        file.write(str.encode('UTF-8'))
    channels = fetch()

    for channel, movies in channels.items():
        with open("%s.html" % channel, "wb") as html:
            render(html, 'channel.tmpl', name=channel, movies=movies)
    with open('index.html', 'wb') as html:
        render(html, 'index.tmpl', channels=sorted(channels.keys()))

if __name__ == '__main__':
    main()

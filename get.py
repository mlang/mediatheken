#!/usr/bin/env python3
from collections import defaultdict
from jinja2 import DictLoader, Environment
from json import loads
from lzma import LZMADecompressor
from re import sub, MULTILINE
from requests import get

response = get('http://m1.picn.de/f/Filmliste-akt.xz')
response.raise_for_status()
data = LZMADecompressor().decompress(response.content).decode('UTF-8')
# Change from dictionary with multiple identical keys to array
data = sub(r'^  "Filmliste" :', "", data, flags=MULTILINE)
data = sub(r'^  "X" :', "", data, flags=MULTILINE)
data = '[' + data[1:-2] + ']'
data = loads(data)
# Remove header
data = data[2:]

header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>{{ title }}</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<body>
'''

footer = '''
</body>
</html>
'''

sender_begin = '''
<h1>>{{name}}</h1>
<ul>
'''

film = '''
<li>{{ date }} {{ time }}: <a href="{{url}}">{{name}}</a></li>
'''

sender_end = '''
</ul>
'''

link_to_sender = '''<a href="{{name}}.html">{{name}}</a> '''

env = Environment(loader=DictLoader(globals()))
def render(file, template, **kwargs):
    print(env.get_template(template).render(kwargs), file=file)
        
sender = None
d = defaultdict(list)
for row in data:
    if len(row[0]) > 0:
        sender = row[0]
    d[sender].append({
        'name': row[2],
        'date': row[3],
        'time': row[4],
        'url': row[8]
    })
data = None
sender = None
for movies in d.values():
    def yyyymmddhhmm(dict):
        date = dict['date']
        if len(date) == 10:
            return date[6:]+date[3:5]+date[0:2]+dict['time']+dict['name']
        else:
            return '0000000000:00:00'+dict['name']
    movies.sort(key=yyyymmddhhmm, reverse=True)

###############################################################################

for sender, filme in d.items():
    with open("%s.html" % sender, "w") as html:
        render(html, 'header', title=sender)
        render(html, 'sender_begin', name=sender)
        for f in filme:
            render(html, 'film', **f)
        render(html, 'sender_end')
        render(html, 'footer')

with open('index.html', 'w') as html:
    render(html, 'header', title='Mediatheken')
    for sender in sorted(d.keys()):
        render(html, 'link_to_sender', name=sender)
    render(html, 'footer')

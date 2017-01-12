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
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<body>
'''

footer = '''
</body>
</html>
'''

sender_begin = '''
<h1><a name="{{name|escape}}">{{name}}</a></h1>
<ul>
'''
film = '''
<li><a href="{{url}}">{{name}}</a></li>
'''
sender_end = '''</ul>'''

link_to_sender = '''<a href="{{name}}.html">{{name}}</a> '''

env = Environment(loader=DictLoader(globals()))
sender= None
d = defaultdict(list)
for row in data:
    if len(row[0]) > 0:
        sender = row[0]
    d[sender].append({'name': row[2], 'url': row[8]})


for sender, filme in d.items():
    with open("%s.html" % sender, "w") as html:
        print(env.get_template('header').render({'title': sender}), file=html)
        print(env.get_template('sender_begin').render({'name': sender}), file=html)
        for f in filme:
            print(env.get_template('film').render(f), file=html)
        print(env.get_template('sender_end').render(), file=html)
        print(env.get_template('footer').render(), file=html)

with open('index.html', 'w') as html:
    print(env.get_template('header').render(), file=html)
    for sender in sorted(d.keys()):
        print(env.get_template('link_to_sender').render({'name': sender}), file=html)
    print(env.get_template('footer').render(), file=html)

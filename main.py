"""Simple REST API for novels

1. GET /work/{id} returns all works or individual works
2. GET /text/{sha1sum} returns plaintext for volume
"""
import asyncio
import collections
import csv
import hashlib
import json
import operator
import os

from aiohttp import web


############################################################################
# load volume metadata stored on disk into memory, indexed by work id
# index text filenames by sha1sum
############################################################################
_volumes = collections.defaultdict(list)
texts = {}
for volumes_dir in ['volumes', 'nonfree']:
    for dirpath, dirnames, filenames in os.walk(volumes_dir):
        for fn in filenames:
            if fn == 'metadata.json':
                metadata = json.load(open(os.path.join(dirpath, fn), encoding='utf8'))
                work_id = int(metadata['work_id'])
                _volumes[work_id] += [metadata]
                # sort volumes in ascending order by volume number
                _volumes[work_id].sort(key=operator.itemgetter('volume'))
            elif os.path.splitext(fn)[-1] == '.txt':
                filename = os.path.join(dirpath, fn)
                sha1 = hashlib.sha1(open(filename, 'rb').read()).hexdigest()
                texts[sha1] = filename

############################################################################
# load work metadata stored on disk into memory
############################################################################
works = collections.OrderedDict((int(d['id']), d) for d in csv.DictReader(open('works.csv', encoding='utf8')))
# insert volumes into relevant work dictionary
for work in works.values():
    # ensure work_id is an integer
    work['id'] = int(work['id'])

    # inject related volume records
    if work['id'] in _volumes:
        work['volumes'] = _volumes[work['id']]

############################################################################
# endpoints
############################################################################

@asyncio.coroutine
def work(request):
    if request.match_info.get('id', None) is None:
        return web.Response(text=json.dumps(works))
    else:
        id = int(request.match_info['id'])
        if id not in works:
            return web.HTTPNotFound
        return web.Response(text=json.dumps(works[id]))

@asyncio.coroutine
def text(request):
    sha1 = request.match_info.get('sha1', None)
    if sha1 is None:
        return web.HTTPNotFound()
    if sha1 not in texts:
        return web.HTTPNotFound()
    else:
        text = open(texts[sha1], encoding='utf8').read()
    return web.Response(text=text)


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/work/', work)
    app.router.add_route('GET', '/work/{id}', work)
    app.router.add_route('GET', '/text/{sha1}', text)

    port = 8080
    srv = yield from loop.create_server(app.make_handler(), '0.0.0.0', port)
    print("Server listening on http://0.0.0.0:{}".format(port))
    print("Serving {} works and {} volumes".format(len(works), len(texts)))
    return srv

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

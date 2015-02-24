"""Simple REST API for novels

1. GET /work/{id} returns all works or individual works
2. GET /text/{sha1sum} returns plaintext for volume
"""
import asyncio
import collections
import csv
import hashlib
import json
import logging
import operator
import os

import aiohttp.web
import requests

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


############################################################################
# urls for bibliographic records and identifiers
############################################################################
# json containing bibliographic records
british_fiction_urls = (
    'https://raw.githubusercontent.com/novels-project/british-fiction-1770-1836/master/data/british-fiction-1800-1829.json',
    'https://raw.githubusercontent.com/novels-project/british-fiction-1770-1836/master/data/british-fiction-1830-1836.json',
    'https://raw.githubusercontent.com/novels-project/british-fiction-1770-1836/master/data/british-fiction-1800-1829-updates.json',
)
british_fiction_annex_url = 'https://github.com/novels-project/british-fiction-1770-1915-annex/raw/master/british-fiction-1770-1915-riddell.json'

# mapping of novels project identifiers to other identifiers
ids_url = 'https://github.com/novels-project/identifiers/raw/master/novels-project-identifiers.json'

############################################################################
# load volume metadata stored on disk into memory, indexed by work id
# index text filenames by sha1sum
############################################################################
def fetch_texts():
    texts = {}
    for volumes_dir in ['volumes', 'nonfree']:
        for dirpath, dirnames, filenames in os.walk(volumes_dir):
            for fn in filenames:
                if os.path.splitext(fn)[-1].startswith('.txt'):
                    filename = os.path.join(dirpath, fn)
                    sha1 = hashlib.sha1(open(filename, 'rb').read()).hexdigest()
                    texts[sha1] = filename
    return texts

def fetch_volumes():
    # NB: metadata.json contains sha1 of relevant text
    volumes = collections.defaultdict(list)
    for volumes_dir in ['volumes', 'nonfree']:
        for dirpath, dirnames, filenames in os.walk(volumes_dir):
            for fn in filenames:
                if fn == 'metadata.json':
                    metadata = json.load(open(os.path.join(dirpath, fn), encoding='utf8'))
                    work_id = int(metadata['work_id'])
                    volumes[work_id] += [metadata]
                    # sort volumes in ascending order by volume number
                    volumes[work_id].sort(key=operator.itemgetter('volume'))
    return volumes

############################################################################
# fetch bibliographic records from version controlled repositories
############################################################################
def fetch_works():
    british_fiction_annex = requests.get(british_fiction_annex_url).json()
    ids_same_as = {int(k): v for k, v in requests.get(ids_url).json().items()}
    ids_same_as_reverse = {v['garside-raven-schöwerling']: k for k, v in ids_same_as.items() if v.get('garside-raven-schöwerling')}
    # populate works dictionary with empty placeholders
    works = collections.OrderedDict((int(id), dict()) for id in sorted(ids_same_as.keys()))
    for url in british_fiction_urls:
        data = requests.get(url).json()
        for source_id, record in data.items():
            id = ids_same_as_reverse[source_id]
            if id not in works:
                raise RuntimeError("Could not find mapping for {}".format(source_id))
            record['source'] = 'garside-raven-schöwerling'
            record['source_id'] = record['id']
            del record['id']
            if works[id]:
                raise ValueError("Found duplicate entry: {}".format(id))
            works[id] = record

    # populate with extra records
    for annex_id, record in british_fiction_annex.items():
        source, source_id = annex_id.split('/')
        record['source'] = source
        if source == 'novels-project':
            source_id = int(source_id)
            id = source_id
        else:
            id = ids_same_as_reverse[source_id]
        record['source_id'] = source_id
        if id not in works:
            raise RuntimeError("Could not find mapping for {}".format(source_id))
        if works[id]:
            raise ValueError("Found duplicate entry: {}".format(id))
        works[id] = record

    # verify that all records are populated and add id to work dictionary
    assert isinstance(id, int)
    for id, record in works.items():
        if not record:
            raise ValueError("Found no information for id {}".format(id))
        works[id]['id'] = id
    return works

############################################################################
# inject volume information into relevant work metadata
############################################################################
def inject_volumes(volumes, works):
    for key, work in works.items():
        assert key == work['id']
        assert isinstance(key, int)
        if work['id'] in volumes:
            work['volumes'] = volumes[work['id']]

############################################################################
# load bibliographic records into memory and inject volume information
############################################################################
# NB: works is a global variable
works = fetch_works()
inject_volumes(fetch_volumes(), works)

############################################################################
# load sha1->filename mapping into memory
############################################################################
# NB: texts is a global variable
texts = fetch_texts()

############################################################################
# endpoints
############################################################################
@asyncio.coroutine
def work(request):
    if request.match_info.get('id', None) is None:
        return aiohttp.web.Response(text=json.dumps(works, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        id = int(request.match_info['id'])
        if id not in works:
            return aiohttp.web.HTTPNotFound
        return aiohttp.web.Response(text=json.dumps(works[id], ensure_ascii=False, indent=2, sort_keys=True))

@asyncio.coroutine
def text(request):
    sha1 = request.match_info.get('sha1', None)
    if sha1 is None:
        return aiohttp.web.HTTPNotFound()
    if sha1 not in texts:
        return aiohttp.web.HTTPNotFound()
    else:
        text = open(texts[sha1], encoding='utf8').read()
    return aiohttp.web.Response(text=text)


@asyncio.coroutine
def index(request):
    text = "See https://novels.io for details."
    return aiohttp.web.Response(text=text)


@asyncio.coroutine
def init(loop):
    app = aiohttp.web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    app.router.add_route('GET', '/work/', work)
    app.router.add_route('GET', '/work/{id}', work)
    app.router.add_route('GET', '/text/{sha1}', text)

    port = 8080
    srv = yield from loop.create_server(app.make_handler(), '0.0.0.0', port)
    logger.info("Server listening on http://0.0.0.0:{}".format(port))
    logger.info("Serving {} works".format(len(works)))
    return srv

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

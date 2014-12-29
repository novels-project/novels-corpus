# Novels Project Corpus

This repository contains all data relevant to the Novels Project. It is under
version control so all changes are recorded.

- `works.csv` contains records of *works* identified by `id`.
- Each directory in `volumes/` corresponds to a *volume*. The directory name is
  unimportant, the file `metadata.json` in each directory describes the
  relationship between the volume and a *work*.

## Quickstart

Work metadata, volume metadata, and plaintext are exposed via a simple
read-only REST server. This server can be run with the following command
(Python 3.4 and `aiohttp` required):

    python main.py

The API has two endpoints:

- `/work` (metadata for all works)
- `/work/<id>`
- `/text/<sha1>`

For example, the novel [Glenarvon](https://en.wikipedia.org/wiki/Glenarvon) has
id `1235` and metadata concerning it and a list of associated volumes may be
retrieved with:

    curl http://127.0.0.1:5000/work/1235

As the plaintext of an edition of this novel is available, a list of associated
texts and their SHA-1 hashes is given in the response.  The plain text version
of the third volume has hash `40d2491e07dd2f1c71413b65bc551804cb93b0f3` and may
be retrieved with:

    curl -s http://127.0.0.1:5000/text/40d2491e07dd2f1c71413b65bc551804cb93b0f3

That's all there is!

## Works

The vast majority of records in `works.csv` are from the two volumes edited by
Garside, Raven, and Schöwerling. There are a handful of additions as well as
some placeholders where data has only been partially entered.

The following fields shall uniquely identify a record:

- `id`
- `source` and `source_id`

## Volumes

Each directory shall contain two files:

- `metadata.json`
- a text file with the extension `.txt`

The SHA1 of the text file is stored in `metadata.json`.

### Metadata

Metadata is associated with each volume that links it to a work.
`metadata.json` contains a JSON-encoded dictionary which shall conform to the
following schema:

- `work_id` the work with which this volume is associated
- `internet_archive_id` Internet Archive id (e.g., `glenarvon01lambc`)
- `volume` integer
- `volume_count` integer (`volume_count` must be greater than or equal to `volume`)
- `date_created` `%Y-%m-%d` of metadata creation
- `date_updated` `%Y-%m-%d` of last metadata update
- `sha1` hex-encoded SHA1 of the text file in the directory
- `extra_info` (optionally empty) dictionary of non-essential information

The following fields uniquely identify a record: `work_id` and `volume`

The text used is the best available facsimile of the original edition
referenced in `works.csv`. The text may be derived from a subsequent edition
(e.g., the second edition) if the subsequent edition is the only one available
or if the scan is of considerably higher quality.

### Texts

A plaintext version of each volume is available. This text is typically the
plaintext derived from Optical Character Recogntion (OCR), trimmed of OCR'd
library stamps and other extraneous material which occurs at the beginning and
ending of the scan. In recognition that this trimming process is not easily
reproducible, *patches* will be provided in a future version that specifies how
to produce the version contained in the repository from the original OCR.

In other cases, particularly when the scan is of very low quality, the
plaintext version may be derived from another source, including manual entry.
All these cases are recorded in `metadata.json`.

## Non-free Volumes

The `nonfree` directory contains volumes and associated plaintexts that are not
available on the Internet Archive. The `metadata.json` conforms to a schema
identical to the one described above but `internet_archive_identifier` is
replaced by `nonfree_identifier`.

If the original source of a plaintext is HTML, a plaintext version is generated
using  [html2text](http://www.mbayer.de/html2text/)  version 1.3.2a.

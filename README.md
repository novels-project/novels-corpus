# Novels Project Library

This repository contains all data relevant to the Novels Project. It is under
version control so all changes are recorded.

- `works.csv` contains records of *works* identified by [`source`, `source_id`]
- Each directory in `volumes/` corresponds to a *volume*. The directory name is
  unimportant, the file `metadata.yml` in each directory describes the
  relationship between the volume and a *work*.

## Works

The vast majority of records in `works.csv` are from the two volumes edited by
Garside, Raven, and Schöwerling. There are a handful of additions as well as
some placeholders where data has only been partially entered.

The following columns SHALL be unique:

- `id`
- `source` and `source_identifier` (together)

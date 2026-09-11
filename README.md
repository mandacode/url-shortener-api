# URL Shortener API

A minimal REST API for shortening URLs. Send a long URL, get a short code back,
resolve that code to the original, or follow it as a redirect.

The feature set is deliberately narrow: two operations and nothing else. Where the
requirements left room for interpretation I made a call and wrote down the reasoning.
Those notes are in [Decisions](#decisions).

## Stack

Python 3.12 · Django 5.2 LTS · Django REST Framework · PostgreSQL · Docker Compose

## Running

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. Migrations run on startup and
PostgreSQL data persists in a named volume.

## Decisions

### Duplicate URLs get separate links

Submitting the same long URL twice creates two independent records with different
codes. Deduplicating would need a unique index on the URL column, which exceeds the
PostgreSQL btree entry size limit for non-ASCII addresses and would require a separate
hash column. It also forces a decision on URL normalisation (is `example.com/a` the
same as `example.com/a/`?) and permanently ties one record to several users, which
rules out per-link expiry and deletion later on. The `url` column carries no index
because nothing ever queries by it.

### Links are immutable

A link is only ever created and read, never updated or deleted, so the table is
append-only by nature and a separate audit trail would add no information. `created_at`
is enough to reconstruct what happened and when.

### Uniqueness is a table constraint, not a field flag

`code` is unique through a `UniqueConstraint` in `Meta` rather than `unique=True` on
the field. On PostgreSQL, field-level uniqueness also creates a companion index with
`varchar_pattern_ops` so that `LIKE` queries can use an index. Codes are only ever
looked up by exact match, so that index would be maintained on every insert and never
read. The constraint gives the same protection, raises the same `IntegrityError` on
conflict, and carries a name I chose rather than a generated one.

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

### Short codes are random, not derived from the primary key

Codes are seven characters drawn from `[0-9a-zA-Z]` with `secrets`. I considered base62
encoding of the auto-increment primary key, which cannot collide and yields the shortest
possible codes. I rejected it: consecutive codes are guessable, so anyone could walk
through other people's links and read off how many records the service holds, and Django
only learns the primary key after the insert, so it would take an insert followed by an
update.

62^7 is roughly 3.5 * 10^12. With a million links stored, the chance that a given insert
lands on a taken code is about one in 3.5 million. Collisions are handled rather than
avoided: the unique constraint rejects the duplicate and the service draws again.

`secrets` rather than `random` is load-bearing. `random` is deterministic and its state
can be reconstructed from enough observed output, which would reintroduce exactly the
predictability I rejected base62 to avoid.

### The repository boundary is what makes the unit tests real

`ShortenerService` depends on a `LinkRepository` protocol rather than on the ORM. The
Django implementation satisfies it structurally, so there is no base class and no
container. The payoff shows up in the tests: service behaviour, including the retry path,
runs against an in-memory fake with no database, which is what makes the split between
unit and end-to-end tests meaningful instead of cosmetic.

Only the repository is injected. `generate_code` is a pure function with no state and no
I/O, so hiding it behind an abstraction would be indirection for its own sake.

### Collisions are settled by the database, not by a lookup

Generating a code and checking whether it is taken before inserting is a time-of-check to
time-of-use race: two workers can both see it as free and both insert. Only the unique
constraint sees uncommitted writes from other transactions, so the service inserts
optimistically and catches `IntegrityError`.

Each attempt sits in its own `transaction.atomic()` block. Django marks a transaction as
needing rollback once an `IntegrityError` escapes it, so a loop wrapped in one outer
atomic block would fail on the second attempt with `TransactionManagementError`. The
inner block is a savepoint that rolls back on its own and leaves the outer transaction
usable.

Attempts are capped at five. At this scale the retry path should never run, so the cap is
not there for collisions but for my own mistakes: a broken generator would otherwise spin
forever instead of surfacing.

# URL Shortener API

A minimal REST API for shortening URLs. Send a long URL, get a short code back,
resolve that code to the original, or follow it as a redirect.

The feature set is deliberately narrow: two operations and nothing else. Where the
requirements left room for interpretation I made a call and wrote down the reasoning.
Those notes are in [Decisions](#decisions).

## Stack

Python 3.12, Django 5.2 LTS, Django REST Framework, PostgreSQL, Docker Compose.

## Running

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`. Migrations run on startup and PostgreSQL
data persists in a named volume.

## API

| Method | Path | Result |
|---|---|---|
| POST | `/api/v1/links/` | 201 with `code`, `short_url` and `url` |
| GET | `/api/v1/links/{code}/` | 200 with the same shape, 404 if unknown |
| GET | `/shrt/{code}` | 302 to the original address, 404 if unknown |

Browsable documentation is at `/api/docs/` and the OpenAPI schema at `/api/schema/`.

## Tests and checks

Unit tests need nothing but the virtualenv, because the service runs against an in-memory
repository:

```bash
uv run pytest tests/unit
```

End-to-end tests go through PostgreSQL, so they run inside the container. This command
runs the whole suite:

```bash
docker compose exec api pytest tests
```

Linting and type checking:

```bash
uv run ruff check .
uv run mypy config shortener tests manage.py
```

Both run on every commit through pre-commit. `mypy` is configured with
`disallow_untyped_defs`, so every function in this repository carries annotations and a
missing one fails the commit instead of being caught in review.

## Layout

```
config/              settings and root URLs
shortener/
  codes.py           short code generation
  models.py          Link
  repositories.py    LinkRepository protocol and the database implementation
  services.py        ShortenerService, retry on collision
  dependencies.py    wires the service together
  views.py           the redirect
  api/               serializers, API views, API URLs
tests/
  unit/              no database
  e2e/               full stack on PostgreSQL
```

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
database implementation satisfies it structurally, so there is no base class and no
container. The payoff is in the tests: the service, including the retry path, runs against
an in-memory implementation with no database at all, which is what makes the split between
unit and end-to-end tests meaningful instead of cosmetic.

Only the repository is injected. `generate_code` is a pure function with no state and no
I/O, so hiding it behind an abstraction would be indirection for its own sake.

### Collisions are settled by the database, not by a lookup

Generating a code and checking whether it is taken before inserting is a time-of-check to
time-of-use race: two workers can both see it as free and both insert. Only the unique
constraint sees uncommitted writes from other transactions, so the insert goes ahead
optimistically and the conflict is caught.

That happens in the repository, not in the service. The insert sits in its own
`transaction.atomic()` block, because Django marks a transaction as needing rollback once
an `IntegrityError` escapes it and the next attempt would fail with
`TransactionManagementError` instead. The repository turns the driver error into
`CodeAlreadyExists`, which is what lets the service be tested without a database.

Attempts are capped at five. At this scale the retry path should never run, so the cap is
not there for collisions but for my own mistakes: a broken generator would otherwise spin
forever instead of surfacing.

### The short domain comes from configuration, not from the request

`short_url` is built from a `SHORT_URL_BASE` setting rather than from
`request.build_absolute_uri()`. In a real deployment the short domain is not the API
domain: the API might live on `api.example.com` while links go out as `exmpl.link/abc123`,
which is the entire point of a shortener. Building the value from the incoming request
would tie it permanently to whichever host the request arrived on, and the `Host` header
is client-supplied and often rewritten by a proxy.

### Only http and https are accepted

The input is a `CharField` with an explicit `URLValidator(schemes=["http", "https"])`
rather than DRF's `URLField`, whose default validator also allows `ftp` and `ftps`.
A shortener is a machine for redirecting people, so the set of schemes it will emit
belongs in an allowlist I wrote down, not in a framework default.

### Both endpoints return the same link representation

A link is `code`, `short_url` and `url`, and both endpoints return that shape.
`short_url` is there so that clients never need to know the path structure: if `/shrt/`
ever changes, a client using the returned value keeps working while one that builds the
address from the code breaks. `code` is the stable identifier a client stores and passes
back to the API, so it never has to be parsed out of a string.

Expanding arguably only needs `url`, since the caller already supplied the code in the
path. I kept one representation anyway: a single serializer is less code than two, clients
parse the same shape whichever endpoint they call, and the OpenAPI schema carries one
model instead of two nearly identical ones. The redundant fields cost a few hundred bytes.

### The service resolves short links itself

"API only" I read as "no frontend", not "no redirect": without a route behind it, the
`short_url` in every response would point at a 404.

Following one returns `302`, not `301`. A `301` is cached by the browser forever, so later
clicks would never reach the service again - ruling out click statistics and deactivating
a link. The route sits at `/shrt/{code}`, outside `/api/` and without a trailing slash,
because every character in a short link is the point.

### Unit tests run without a database

`tests/unit` exercises the service against an in-memory repository: no container, no
database, no fixtures, well under a second. Writing them is what exposed the leak the
refactor fixed - `transaction.atomic()` opens a connection on entry, so a service holding
its own transaction could never have been tested this way.

The collision path is covered by a repository that refuses the first N codes. A real race
cannot be tested reliably, since a threaded test passes or fails on timing, so it is split
in two: the retry logic here, and the existence of the unique constraint in the
end-to-end tests.

### End-to-end tests go through the whole stack

`tests/e2e` drives the real URL routing, serializers, service, repository and PostgreSQL
with DRF's `APIClient`. Between them the cases cover both operations the requirements ask
for, the redirect, the two rejection paths for bad input, and the fact that one URL
submitted twice produces two codes that both resolve.

One case does not touch the API at all: it inserts the same code twice through the ORM and
expects an `IntegrityError`. A `UniqueConstraint` declared on a model guarantees nothing
until a migration applies it, so this asserts that the constraint is really in the
database. Together with the retry test in `tests/unit`, that covers both halves of the
concurrency story without a flaky threaded test.

### The schema is generated, not written

`drf-spectacular` builds the OpenAPI document from the serializers and the URL patterns,
so the documentation cannot drift away from the code. The two views are plain `APIView`
classes, which carry no serializer attribute to infer from, so each one declares its
request and response shapes explicitly, error responses included. An end-to-end test
requests the schema, because it is generated at runtime and a broken annotation would
otherwise stay unnoticed until somebody opened the docs.


## What I left out

No authentication, no expiry, no custom aliases, no click statistics, no rate limiting.
The requirements asked for a narrow feature set, and each of these is a product decision
rather than a missing piece.

At a scale where they mattered, the service would change in predictable ways. A shortener
reads far more often than it writes, so the code-to-URL mapping would go behind a cache
before anything else. A seven character code is guessable by brute force given enough
requests, so the answer to scanning is a rate limiter, not a longer code. Click statistics
would be an append-only table written asynchronously through a queue, never a counter
updated inside the redirect, which has to stay fast. Deployments would replace the
development server with a WSGI server and drop `--no-dev` into the image build. None of
that is here, because none of it is justified by two endpoints.

## License

MIT, see [LICENSE](LICENSE).

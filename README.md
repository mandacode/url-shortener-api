# URL Shortener API

A minimal REST API for shortening URLs. Send a long URL, get a short code back,
resolve that code to the original, or follow it as a redirect.

The feature set is deliberately narrow: two operations and nothing else. Where the
requirements left room for interpretation I made a call and wrote down the reasoning.
Those notes are in [Decisions](#decisions).

## Stack

Python 3.12 · Django 5.2 LTS · Django REST Framework · PostgreSQL · Docker Compose

## Decisions

Recorded as the project progresses, each one at the point it was made.

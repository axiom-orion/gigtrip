# Security policy

## Supported versions

Only the `main` branch is supported. There are no maintained release branches; fixes land on `main`.

## Reporting a vulnerability

Please report security issues privately, not in public issues or pull requests:

- Use GitHub's private vulnerability reporting on this repository (**Security → Report a vulnerability**), or
- Email **security@vorion.org**.

Include what you found, how to reproduce it, and the impact you expect. We aim to reply within 7 days.

## Scope

gigtrip is a pure-Python optimiser (standard library only), an offline eval script, and an optional Streamlit app. It makes no LLM calls and has no backend, accounts or payments. Relevant reports include:

- **The `BANDSINTOWN_APP_ID` key** — anything that would leak it (for example into logs, error output or the rendered page), or code that hardcodes or commits a key.
- **The live Bandsintown request** — artist names typed into the app are placed into the request URL; malformed or crafted input that changes the request beyond the intended artist lookup.
- **The Streamlit UI** — user input rendered as Markdown or links (for example the city in the Concierge links) in a way that allows script or link injection.
- **File writes** — `eval/run_eval.py` writes `eval/results.md` and `eval/results.json`; anything that makes it write elsewhere.
- **Dependencies** — known-vulnerable versions pinned in `pyproject.toml` or `requirements.txt`.

Out of scope: the synthetic corpus in `data/events.json`, and the third-party services (Bandsintown, Ticketmaster, Booking.com) themselves.

# Terror Zone Telebot

Telegram bot that tells Diablo II: Resurrected players which zone is terrorised
right now, warns them 15 minutes before it rotates, and only pings them about
the zones they actually farm.

[![CI](https://github.com/cprite/terror-zone-telebot/actions/workflows/ci.yml/badge.svg)](https://github.com/cprite/terror-zone-telebot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What it does

- **Rotation alerts.** A heads-up 15 minutes before the zone changes, and a
  message the moment it does.
- **Zone filter.** Pick from the 36 terror zone groups; pick none and you get
  everything.
- **Current zone on demand.** What is terrorised now and what is next.
- **Six interface languages** - English, Russian, Ukrainian, Chinese,
  Portuguese, German - auto-selected from the user's Telegram client, and
  changeable from the menu.
- **Admin panel** for announcements, a time-boxed advert, maintenance mode and
  subscriber stats.

## How it works

```
d2runewizard.com/api  --poll every 60s-->  Tracker  -->  SQLite
     (JSON, cached)                          |         (subscribers,
                                             |          zone filters)
                                             v
                                        Broadcaster  --> Telegram
                                     (rate-limited fan-out)
```

One background task polls the tracker for everyone. When the reported zone
changes, subscribers whose filter matches get a message; the 15-minute warning
fires once per hour, off the same snapshot. Subscriptions, zone filters and
language live in SQLite, so a restart or redeploy loses nothing.

### Where the data comes from

[D2Runewizard's terror zone tracker](https://d2runewizard.com/integration)
publishes a JSON endpoint that is CDN-cached for 60 seconds. The bot polls it
and identifies itself with the `D2R-Contact` / `D2R-Platform` / `D2R-Repo`
headers the site asks integrations to send.

The endpoint answers without a token. Setting `D2RW_TOKEN` unlocks their richer
payload (report counts and confidence); the bot reads either shape.

Zone names are matched by significant words rather than by string equality,
because the upstream spells the same zone several ways - `Chaos Sanctuary` and
`The Chaos Sanctuary`, or the short and long forms of Nihlathak's Temple. An
unrecognised name is still relayed verbatim rather than dropped, and logged as
a warning so the table can be updated.

## Quick start

### Docker

```bash
git clone https://github.com/cprite/terror-zone-telebot.git
cd terror-zone-telebot
cp .env.example .env      # put your BOT_TOKEN and ADMIN_IDS in
docker compose up -d
```

The SQLite file lives in a named volume, so `docker compose up --build` keeps
your subscribers.

### Locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env      # put your BOT_TOKEN and ADMIN_IDS in
python -m tzbot
```

### Platform-as-a-service

`Procfile` runs a single `worker` process, so Heroku, Railway, Render and
friends need no extra configuration - set the same environment variables in
the dashboard. Note that SQLite on an ephemeral filesystem is wiped on every
deploy; mount a persistent disk if the platform offers one.

## Configuration

Everything is read from the environment, or from a `.env` file next to the
project. See [`.env.example`](.env.example).

| Variable | Default | Meaning |
| --- | --- | --- |
| `BOT_TOKEN` | *required* | Token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | *(empty)* | Comma-separated Telegram user IDs allowed into the admin panel. Empty means nobody. |
| `DATABASE_PATH` | `data/tzbot.sqlite3` | Where SQLite keeps state |
| `POLL_INTERVAL` | `60` | Seconds between polls; the upstream caches for 60 |
| `PREALERT_MINUTE` | `45` | Minute of the hour (UTC) for the "15 minutes left" warning |
| `BROADCAST_RATE` | `25` | Messages per second during a fan-out; Telegram throttles near 30 |
| `D2RW_CONTACT` | *(empty)* | Contact email sent to the tracker |
| `D2RW_PLATFORM` | `Telegram` | Platform name sent to the tracker |
| `D2RW_REPO` | this repo | Public repo URL sent to the tracker |
| `D2RW_TOKEN` | *(empty)* | Optional D2Runewizard token |

`ADMIN_IDS` is deliberately not in the source. Get yours from
[@userinfobot](https://t.me/userinfobot).

## Development

```bash
pip install -e ".[dev]"
pytest          # the whole suite runs offline
ruff check src tests
```

Tests cover zone-name matching against real strings the tracker has emitted,
storage behaviour, rotation and pre-alert timing, delivery semantics, and a
regression suite pinning the admin panel shut against non-admins.

## Project history

Written in 2024 and shelved: it read the zone off a community site with headless
Chrome and BeautifulSoup, which the site's terms did not allow and which got
blocked often enough to make the bot unreliable.

The 2.0 rewrite replaces scraping with the documented JSON API - no Selenium, no
Chrome, no browser buildpack - and rebuilds what had grown around it:

- **Admin panel was unguarded.** Rights were checked where the button was drawn,
  never where the action ran. Callback data is attacker-controlled, so any user
  could broadcast to the whole base, set an advert or toggle maintenance. The
  guard now sits on the router, so no handler can be added without it.
- **One `while True` loop per user**, inside a callback handler, ticking every
  second with the subscription held in memory. Now: one poller, state in SQLite.
- **A CSV rewritten through pandas** on every toggle. Now: SQLite.
- **A bare `except` that deleted the subscriber** on any send failure, so a
  network blip cost a real user. Now: only Telegram saying the user is gone
  deactivates them, and the row and their zone filter survive.

## License

MIT - see [LICENSE](LICENSE).

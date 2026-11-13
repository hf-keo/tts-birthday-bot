# 🎂 TTS Birthday Bot

A multi-server Discord birthday calendar, ready for Python hosting on Enzonic.

## Features

- `/birthday register`: private modal accepting **day and month only**, no year or age.
- `/birthday remove`: delete your own entry in this server.
- `/birthday list [page]`: all server birthdays, calendar order, 15 per page.
- `/birthday upcoming [page]`: birthdays sorted by next occurrence, with days remaining.
- `/birthday setup`: Manage Server permission required; interactive channel, ping mode and optional role selectors. Save enables announcements.
- `/birthday pause`: disable announcements; save setup again to resume.
- `/birthday admin-set member` and `/birthday admin-remove member`: Manage Server controls.
- Random choice of six preset wishes; edit `WISHES` in `birthday_bot/core.py` to add more.
- Midnight **Asia/Kuala_Lumpur (UTC+8)** birthdays, checked every 30 seconds, independent of host timezone.
- SQLite created automatically on persistent host storage. Every entry, setting and delivery is keyed by Discord guild ID. Different servers have isolated records in **one SQLite file**, not a separate physical file per server.
- Explicit allowed mentions: birthday user, selected role, both, or nobody. Never pings @everyone or @here.

## Quick start

Requires Python 3.11–3.13. Python 3.12 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Set DISCORD_TOKEN securely in your environment, then:
python -m birthday_bot
```

On Windows, activate with `.venv\Scripts\activate`. The application reads environment variables directly; `.env.example` is a reference, not an automatically loaded configuration file.

| Variable | Required | Default |
|---|---|---|
| `DISCORD_TOKEN` | Yes | none |
| `DATABASE_PATH` | No | `data/birthdays.sqlite3` |

Create an application and bot in the [Discord Developer Portal](https://discord.com/developers/applications). Install it to your server with the `bot` and `applications.commands` scopes. Give View Channel, Send Messages and Embed Links in channels where it is used. Administrator permission and privileged gateway intents are **not required**. For role pings, make that role mentionable or grant Mention Everyone in the announcement channel only. The bot still explicitly disallows everyone/here mentions.

After startup, commands are synced globally (Discord propagation may take time). Run `/birthday setup`, select the channel and ping mode, then Save. Each server must run its own setup.

Full hosting walkthrough: [Enzonic deployment](docs/ENZONIC.md).

## Scheduling and reliability

The first tick after readiness checks today's Malaysian date, then repeats every 30 seconds. While online, delivery normally occurs within 30 seconds of midnight plus Discord/API latency. If restarted later that day, unsent birthdays are announced then. Birthdays registered during their birthday can be announced on the next tick. Prior days are not replayed. February 29 is celebrated on February 28 in non-leap years.

A durable per-server/user/date delivery ledger suppresses repeat sends after normal restarts and allows retry after a reported send failure. Failures are logged and retried on the next tick; other deliveries continue. Departed members are removed when their scheduled birthday is checked.

Run **one bot process** against the database. Exactly-once delivery across SQLite and Discord is impossible: if a process dies after claiming but before completing, its `pending` delivery stays suppressed to avoid duplicates. A Discord request accepted before a network error may also be retried. See recovery instructions below. Discord outages, rate limits and host downtime can delay messages.

## Data and privacy

Birthdays are visible to members through commands; registration explicitly explains this. Responses and setup menus are ephemeral. No year, age, message content or token is stored in the database. Admins should obtain permission before entering someone else's birthday. `/birthday remove` deletes the birthday entry; historical delivery keys remain for deduplication. The host operator can access the database. Leaving a server does not immediately erase its records.

Database tables are `birthdays`, `settings` and `deliveries`; schema creation is idempotent. SQLite uses WAL mode. Small transactions run synchronously on the event loop, suitable for a community bot; high-volume deployments should move database work to a dedicated async storage layer.

### Backup and recovery

Stop the bot before copying the database and restart afterward, or use SQLite's online backup API (do not copy only the main file while WAL writes are active). Store backups securely outside the public repository. Restore with the bot stopped, to the same `DATABASE_PATH`.

After an interrupted delivery, stop the bot and inspect uncertain claims:

```sql
SELECT * FROM deliveries WHERE state = 'pending';
```

Check the announcement channel first. If the message exists, set that exact row's state to `sent`. If absent, delete only that exact row (matching guild_id, user_id, birthday). Restarting on the same Malaysian calendar day retries it. Never clear the whole ledger to fix one delivery.

## Development and tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

Tests use temporary databases and mocked Discord interactions; no token needed. They cover date validation, leap dates, rollover, guild isolation, persistence, pause/resume, retry, deduplication, Malaysia midnight conversion, command schema, pagination, mention restrictions, modal input and admin checks. GitHub Actions runs this suite on Python 3.11, 3.12 and 3.13.

Live gateway login, Discord permission behavior and an actual Enzonic deployment require your own token and host access. Use a test server: setup a private channel, register today's day/month, verify one wish, restart and confirm no second wish. Test each ping mode with a test role; then remove the test birthday and configure your production channel.

## Repository hygiene

Tokens belong only in host environment variables. Runtime SQLite files, WAL files, `.env`, caches and virtual environments are ignored. No seeded database or real member records are shipped. Do not enable shell tracing when configuring secrets. Rotate a token immediately if it is ever exposed.

## References

- [discord.py interactions](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- [discord.py task helpers](https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html)
- [Enzonic Python hosting](https://www.enzonic.com/python)
- [Enzonic discord.py hosting](https://enzonic.com/discord-bots/discord-py)

# Verification report

Verified locally on 13 November 2026 using Python 3.12.14 and discord.py 2.6.4.

- `python -m pytest -q`: **38 passed**, 0 failed (0.45 seconds).
- `python -m pip check`: no broken requirements.
- `python -m compileall -q birthday_bot main.py`: passed.
- One upstream Python 3.12 deprecation warning: discord.py imports audioop; it does not affect this bot's text-only behavior.
- Source archive includes no real tokens, runtime databases, virtual environments or caches. `.env.example` contains a placeholder only.
- Tests cover invalid/valid dates, leap birthdays, year rollover, timezone conversion at Malaysia midnight, settings, persistence, guild isolation, deduplication, retry and failure isolation, permission guards, modal validation, paginated listings, all ping modes, setup validation and departed-member removal.

## External checks not completed

GitHub read access worked, but the connector's Contents write request returned HTTP 403 `Resource not accessible by integration`. The browser was signed out. No files or commits were published remotely, so GitHub Actions has not run. The configured CI matrix is Python 3.11, 3.12 and 3.13; only 3.12 was run locally.

No Discord bot token or Enzonic host access was supplied. Actual Discord login, command synchronization, notification delivery and host persistence remain to be checked using the smoke test in `ENZONIC.md`.

## Publish from a GitHub-authenticated local checkout

Extract the archive into the empty repository checkout, including `.github/`, `.gitignore` and `.env.example`, then:

```bash
git add .
git commit -m "Build TTS Birthday Bot with setup UI, SQLite and scheduler"
git push origin main
```

Check the Actions tab after pushing. Do not copy a real `.env` or `data/` directory into the checkout.

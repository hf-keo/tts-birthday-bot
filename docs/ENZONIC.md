# Deploy to Enzonic

Use a **Python / Discord bot hosting service** for this bot. A Project Zomboid game-server instance is a different runtime; do not overwrite your game server. Enzonic documents Python runtimes, startup commands and environment variables; exact panel labels depend on your selected template.

## 1. Prepare Discord

1. Open https://discord.com/developers/applications and create an application named TTS Birthday Bot (or use your existing application).
2. Open Bot and generate/reset the bot token. Put it directly into the hosting panel secret variable; do not paste it into GitHub, chat, or a startup command.
3. Use OAuth2 URL Generator / Installation with **Guild Install**, scopes `bot` and `applications.commands`. Permissions: View Channels, Send Messages and Embed Links. Invite to your server with an account allowed to manage it.
4. No Message Content, Server Members or Presence privileged intent is required. The birthday sender fetches the specific member through the API.

## 2. Upload the code

1. Create/open a Python bot instance, choose Python **3.12** where available, and stop it while configuring.
2. Import `https://github.com/hf-keo/tts-birthday-bot.git` using the panel Git feature, or download the GitHub ZIP and upload/extract it with File Manager/SFTP.
3. Ensure `requirements.txt`, `main.py` and `birthday_bot/` are at the startup working directory root, usually `/home/container`. Avoid a nested `tts-birthday-bot-main/` directory.
4. Configure the panel dependency install step to run `python -m pip install -r requirements.txt` (some Python templates do this automatically).
5. Set the startup command to **`python -m birthday_bot`**. If the template only accepts a Python filename, set it to **`main.py`**, the included entry-point wrapper.

## 3. Set variables and persistent storage

In Startup / Variables / Environment, configure:

| Name | Value |
|---|---|
| `DISCORD_TOKEN` | Your private Discord bot token |
| `DATABASE_PATH` | `/home/container/data/birthdays.sqlite3` |

Confirm that `/home/container/data` is writable and **persists across restarts, reinstallations and code updates** for your plan. If your host provides a different persistent mount, use that path instead. The directory and database are created at startup; do not upload a blank database. No external MySQL service or public port is needed. If the panel cannot define custom variables, ask Enzonic to enable them; this project does not read a token from a file.

Use one running instance. Enable the panel's restart-on-crash feature where offered. The machine's timezone does not affect scheduling.

## 4. Start and configure

1. Start and check the console for successful Discord login / gateway connection. A missing token fails with a clear message.
2. In Discord, wait for slash commands to appear, then run `/birthday setup` as a member with Manage Server permission.
3. Select the announcement text channel, select the ping mode, optionally select a role, then press **Save configuration**. The setup menu expires after three minutes; reopen it if needed.
4. The bot needs View Channel and Send Messages there. For role mode/both, make the role mentionable or grant Mention Everyone in that channel. @everyone cannot be selected as the birthday role.
5. Register with `/birthday register`, entering numeric day and month. `/birthday list` and `/birthday upcoming` show the server calendar.

## 5. Smoke test

In a test server/channel, register today's Malaysian day/month. The scheduler should post on its next tick (within roughly 30 seconds while healthy). Restart the bot and check that it does not post again. Try each ping mode using a test role. Remove the test entry afterward. A stored delivery for today intentionally prevents a second test message for the same user/server/date; use another test member/server rather than deleting production delivery history.

## Updates and backups

Stop the bot, back up `data/`, update code and install requirements, then restart. Do not delete/replace `data/` during reinstall or ZIP extraction. See README for safe SQLite backup and uncertain-delivery recovery. Code updates do not require re-registering birthdays if the database path stays the same.

## Troubleshooting

| Symptom | Check |
|---|---|
| Missing `DISCORD_TOKEN` | Exact variable name, save panel settings and restart |
| `ModuleNotFoundError` | Install requirements using the same Python used at startup |
| No slash commands | Correct bot invited with applications.commands; allow propagation; check startup sync errors |
| No announcement | Setup saved, not paused, correct Malaysian date, channel access, member still present; inspect logs |
| Role shown but not notified | Role mentionable or bot has Mention Everyone; Discord/member notification settings can suppress notifications |
| Birthday already sent today | Delivery ledger prevents repeated messages after restarts |
| Data disappears | Wrong database path or nonpersistent filesystem; restore backup to persistent mount |
| Menu stops responding | Reopen /birthday setup after its 3-minute timeout |

Official hosting references: https://www.enzonic.com/python and https://enzonic.com/discord-bots/discord-py . No host account or live token is required to run the automated tests.

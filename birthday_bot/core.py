"""Date rules, guild-scoped persistence and announcement delivery."""
import calendar
import random
import sqlite3
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MYT = ZoneInfo('Asia/Kuala_Lumpur')
WISHES = (
    '🎂 Happy birthday, {user}! Wishing you an amazing year ahead! 🎉',
    '🎉 It’s {user}’s birthday! May your day be full of joy and cake! 🍰',
    '🥳 Happy birthday, {user}! Here’s to new adventures and great memories!',
    '🎈 Sending birthday cheers to {user}! Have a wonderful celebration! 🎂',
    '🌟 Happy birthday, {user}! Wishing you happiness, health and success!',
    '🍰 A special day for {user}! Happy birthday from all of us! 🎊',
)


def validate(day: int, month: int):
    date(2000, month, day)  # Leap birthdays are valid; no birth year retained.


def occurrence(day: int, month: int, year: int) -> date:
    return date(year, month, 28 if month == 2 and day == 29 and not calendar.isleap(year) else day)


def next_birthday(day: int, month: int, today: date) -> date:
    target = occurrence(day, month, today.year)
    return target if target >= today else occurrence(day, month, today.year + 1)


class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS settings (
          guild_id INTEGER PRIMARY KEY, channel_id INTEGER NOT NULL,
          ping_mode TEXT NOT NULL CHECK(ping_mode IN ('user','role','both','none')),
          role_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS birthdays (
          guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
          day INTEGER NOT NULL, month INTEGER NOT NULL,
          PRIMARY KEY(guild_id,user_id));
        CREATE TABLE IF NOT EXISTS deliveries (
          guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
          birthday TEXT NOT NULL, state TEXT NOT NULL,
          PRIMARY KEY(guild_id,user_id,birthday));
        ''')
        self.conn.commit()

    def set_birthday(self, guild, user, day, month):
        validate(day, month)
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO birthdays VALUES (?,?,?,?)', (guild,user,day,month))

    def remove(self, guild, user):
        with self.conn:
            self.conn.execute('DELETE FROM birthdays WHERE guild_id=? AND user_id=?', (guild,user))

    def birthdays(self, guild):
        return self.conn.execute('SELECT * FROM birthdays WHERE guild_id=? ORDER BY month,day,user_id', (guild,)).fetchall()

    def configure(self, guild, channel, mode, role=None):
        if mode not in ('user','role','both','none'):
            raise ValueError('Invalid ping mode.')
        if mode in ('role','both') and role is None:
            raise ValueError('Choose a role for this ping mode.')
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO settings VALUES (?,?,?,?,1)', (guild,channel,mode,role))

    def settings(self):
        return self.conn.execute('SELECT * FROM settings WHERE enabled=1').fetchall()

    def pause(self, guild):
        with self.conn:
            self.conn.execute('UPDATE settings SET enabled=0 WHERE guild_id=?', (guild,))

    def claim(self, guild, user, birthday):
        with self.conn:
            result = self.conn.execute('INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?)', (guild,user,birthday,'pending'))
        return result.rowcount == 1

    def finish(self, guild, user, birthday, success):
        with self.conn:
            if success:
                self.conn.execute('UPDATE deliveries SET state=? WHERE guild_id=? AND user_id=? AND birthday=?', ('sent',guild,user,birthday))
            else:
                self.conn.execute('DELETE FROM deliveries WHERE guild_id=? AND user_id=? AND birthday=?', (guild,user,birthday))

    def close(self):
        self.conn.close()


class Scheduler:
    def __init__(self, db, send, logger):
        self.db, self.send, self.logger = db, send, logger

    async def run(self, now=None):
        now = now or datetime.now(MYT)
        if now.tzinfo is None:
            raise ValueError('Scheduler requires an aware datetime.')
        today = now.astimezone(MYT).date()
        for config in self.db.settings():
            for row in self.db.birthdays(config['guild_id']):
                if occurrence(row['day'],row['month'],today.year) != today:
                    continue
                key = (row['guild_id'],row['user_id'],today.isoformat())
                if not self.db.claim(*key):
                    continue
                try:
                    await self.send(config, row, random.choice(WISHES))
                except Exception:
                    self.db.finish(*key, False)
                    self.logger.exception('Birthday delivery failed for guild=%s user=%s', *key[:2])
                else:
                    self.db.finish(*key, True)

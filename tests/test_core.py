import logging
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from birthday_bot.core import Database, Scheduler, MYT, next_birthday, validate

@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path/'birthdays.sqlite3')
    yield database
    database.close()

@pytest.mark.parametrize('day,month', [(1,1),(31,12),(29,2),(30,4)])
def test_valid_dates(day,month):
    validate(day,month)

@pytest.mark.parametrize('day,month', [(0,1),(32,1),(31,4),(30,2),(1,13)])
def test_invalid_dates(day,month):
    with pytest.raises(ValueError): validate(day,month)

def test_guild_isolation_and_update(db):
    db.set_birthday(1,7,5,6)
    db.set_birthday(2,7,8,9)
    db.set_birthday(1,7,10,11)
    assert len(db.birthdays(1)) == 1
    assert db.birthdays(1)[0]['day'] == 10
    db.remove(1,7)
    assert not db.birthdays(1)
    assert db.birthdays(2)[0]['day'] == 8

def test_settings_pause_and_validation(db):
    with pytest.raises(ValueError): db.configure(1,2,'role')
    with pytest.raises(ValueError): db.configure(1,2,'invalid')
    db.configure(1,2,'both',3)
    db.configure(2,8,'none')
    db.pause(1)
    assert [r['guild_id'] for r in db.settings()] == [2]
    db.configure(1,4,'user')
    assert len(db.settings()) == 2

def test_persistence(tmp_path):
    path = tmp_path/'persistent.sqlite3'
    db = Database(path)
    db.set_birthday(1,2,3,4)
    db.configure(1,5,'user')
    assert db.claim(1,2,'2026-04-03')
    db.finish(1,2,'2026-04-03',True)
    db.close()
    db = Database(path)
    assert db.birthdays(1)[0]['month'] == 4
    assert len(db.settings()) == 1
    assert not db.claim(1,2,'2026-04-03')
    db.close()

@pytest.mark.parametrize('day,month,today,expected', [
    (1,1,date(2026,12,31),date(2027,1,1)),
    (13,11,date(2026,11,13),date(2026,11,13)),
    (29,2,date(2027,2,1),date(2027,2,28)),
    (29,2,date(2028,2,1),date(2028,2,29)),
    (29,2,date(2027,3,1),date(2028,2,29)),
])
def test_next_birthday(day,month,today,expected):
    assert next_birthday(day,month,today) == expected

@pytest.mark.asyncio
async def test_malaysia_midnight_dedup_and_new_year(db):
    db.configure(1,10,'user')
    db.set_birthday(1,7,1,1)
    send = AsyncMock()
    scheduler = Scheduler(db,send,logging.getLogger('test'))
    await scheduler.run(datetime(2026,12,31,15,59,tzinfo=timezone.utc))
    send.assert_not_awaited()
    await scheduler.run(datetime(2026,12,31,16,0,tzinfo=timezone.utc))
    await scheduler.run(datetime(2027,1,1,12,0,tzinfo=MYT))
    assert send.await_count == 1
    await scheduler.run(datetime(2028,1,1,tzinfo=MYT))
    assert send.await_count == 2

@pytest.mark.asyncio
async def test_failure_retry_and_other_guild_continues(db):
    for guild in (1,2):
        db.configure(guild,10,'none')
        db.set_birthday(guild,7,13,11)
    send = AsyncMock(side_effect=[RuntimeError('unavailable'),None,None])
    scheduler = Scheduler(db,send,logging.getLogger('test'))
    now = datetime(2026,11,13,9,tzinfo=MYT)
    await scheduler.run(now)
    await scheduler.run(now)
    assert send.await_count == 3

@pytest.mark.asyncio
async def test_pause_leap_and_unconfigured(db):
    db.configure(1,10,'none')
    db.configure(2,10,'none')
    db.pause(2)
    for guild in (1,2,3): db.set_birthday(guild,7,29,2)
    send = AsyncMock()
    scheduler = Scheduler(db,send,logging.getLogger('test'))
    await scheduler.run(datetime(2027,2,28,tzinfo=MYT))
    assert send.await_count == 1
    assert send.call_args.args[0]['guild_id'] == 1

@pytest.mark.asyncio
async def test_naive_time_rejected(db):
    with pytest.raises(ValueError):
        await Scheduler(db,AsyncMock(),logging.getLogger('test')).run(datetime(2026,1,1))

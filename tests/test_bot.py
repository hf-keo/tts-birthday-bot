from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord import app_commands
from birthday_bot.bot import BirthdayBot, Birthdays, BirthdayModal, SetupView
from birthday_bot.core import Database

@pytest.fixture
def db(tmp_path):
    obj = Database(tmp_path/'db.sqlite3')
    yield obj
    obj.close()


def interaction():
    return SimpleNamespace(guild_id=1,user=SimpleNamespace(id=7),permissions=SimpleNamespace(manage_guild=True),response=SimpleNamespace(send_message=AsyncMock(),defer=AsyncMock(),edit_message=AsyncMock(),send_modal=AsyncMock()))

@pytest.mark.asyncio
async def test_command_schema_and_admin_checks(db):
    group = Birthdays(db)
    schema = group.to_dict(discord.app_commands.CommandTree(discord.Client(intents=discord.Intents.none())))
    assert schema['dm_permission'] is False
    assert {x.name for x in group.commands} == {'register','remove','list','upcoming','setup','pause','admin-set','admin-remove'}
    i = interaction()
    i.permissions.manage_guild = False
    for name in ('setup','pause','admin-set','admin-remove'):
        command = group.get_command(name)
        assert command.checks
        with pytest.raises(app_commands.MissingPermissions):
            await command.checks[0](i)

@pytest.mark.asyncio
async def test_modal_valid_and_invalid(db):
    modal = BirthdayModal(db,1,7)
    modal.day._value = '29'
    modal.month._value = '2'
    i = interaction()
    await modal.on_submit(i)
    assert db.birthdays(1)[0]['day'] == 29
    modal.day._value = '31'
    await modal.on_submit(i)
    assert db.birthdays(1)[0]['day'] == 29
    assert 'valid' in i.response.send_message.call_args.args[0]

@pytest.mark.asyncio
async def test_setup_owner_and_permission_guard(db):
    view = SetupView(db,7)
    i = interaction()
    assert await view.interaction_check(i)
    i.user.id = 8
    assert not await view.interaction_check(i)
    i.user.id = 7
    i.permissions.manage_guild = False
    assert not await view.interaction_check(i)

@pytest.mark.asyncio
async def test_setup_rejects_missing_choices(db):
    view = SetupView(db,7)
    i = interaction()
    await view.save.callback(i)
    assert not db.settings()

@pytest.mark.asyncio
async def test_listing_paginates_and_never_pings(db):
    for user in range(32): db.set_birthday(1,user,1,1)
    db.set_birthday(2,999,1,1)
    i = interaction()
    await Birthdays(db).show(i,2,True)
    kwargs = i.response.send_message.call_args.kwargs
    assert len(kwargs['embed'].description.splitlines()) == 15
    assert '999' not in kwargs['embed'].description
    assert not kwargs['allowed_mentions'].users
    await Birthdays(db).show(i,9,False)
    assert 'between 1 and 3' in i.response.send_message.call_args.args[0]

@pytest.mark.asyncio
@pytest.mark.parametrize('mode,users,roles',[('user',True,False),('role',False,True),('both',True,True),('none',False,False)])
async def test_announcement_mentions(tmp_path,mode,users,roles):
    bot = BirthdayBot(tmp_path/'bot.sqlite3')
    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    member = SimpleNamespace(id=7,mention='<@7>',display_name='@everyone')
    role = SimpleNamespace(id=8,mention='<@&8>',is_default=lambda:False)
    guild = SimpleNamespace(fetch_member=AsyncMock(return_value=member),get_channel=lambda _:channel,get_role=lambda _:role)
    bot.get_guild = lambda _:guild
    await bot.send_birthday({'guild_id':1,'channel_id':10,'role_id':8,'ping_mode':mode},{'user_id':7},'Happy birthday {user}')
    allowed = channel.send.call_args.kwargs['allowed_mentions']
    assert bool(allowed.users) == users
    assert bool(allowed.roles) == roles
    assert allowed.everyone is False
    await bot.close()

@pytest.mark.asyncio
async def test_modal_rechecks_admin_permission(db):
    modal = BirthdayModal(db,1,99)
    modal.day._value, modal.month._value = '5','6'
    i = interaction()
    i.permissions.manage_guild = False
    await modal.on_submit(i)
    assert not db.birthdays(1)

@pytest.mark.asyncio
@pytest.mark.parametrize('mode,role_ok,mentionable,can_mention,expected',[
    ('user',False,False,False,True),
    ('none',False,False,False,True),
    ('role',False,False,False,False),
    ('both',True,False,False,False),
    ('role',True,True,False,True),
    ('both',True,False,True,True),
])
async def test_setup_save_validation(db,mode,role_ok,mentionable,can_mention,expected):
    view = SetupView(db,7)
    view.channel,view.mode,view.role = 10,mode,8
    permissions = SimpleNamespace(send_messages=True,view_channel=True,mention_everyone=can_mention)
    channel = SimpleNamespace(permissions_for=lambda _:permissions)
    role = SimpleNamespace(is_default=lambda:False,mentionable=mentionable) if role_ok else None
    i = interaction()
    i.guild = SimpleNamespace(get_channel=lambda _:channel,get_role=lambda _:role,me=object())
    await view.save.callback(i)
    assert bool(db.settings()) is expected
    if expected:
        assert db.settings()[0]['ping_mode'] == mode
        assert all(child.disabled for child in view.children)

@pytest.mark.asyncio
async def test_departed_member_removed(tmp_path):
    bot = BirthdayBot(tmp_path/'bot.sqlite3')
    bot.db.set_birthday(1,7,1,1)
    response = SimpleNamespace(status=404,reason='Not Found')
    guild = SimpleNamespace(id=1,fetch_member=AsyncMock(side_effect=discord.NotFound(response,'Unknown member')))
    bot.get_guild = lambda _:guild
    await bot.send_birthday({'guild_id':1},{'user_id':7},'Hi {user}')
    assert not bot.db.birthdays(1)
    await bot.close()

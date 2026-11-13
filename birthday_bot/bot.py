import logging
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .core import Database, MYT, Scheduler, next_birthday
from datetime import datetime

log = logging.getLogger(__name__)


class BirthdayModal(discord.ui.Modal, title='Register birthday'):
    day = discord.ui.TextInput(label='Day (1–31)', max_length=2)
    month = discord.ui.TextInput(label='Month (1–12)', max_length=2)

    def __init__(self, db, guild, user):
        super().__init__()
        self.db, self.guild, self.user = db, guild, user

    async def on_submit(self, interaction):
        if interaction.guild_id != self.guild or (interaction.user.id != self.user and not interaction.permissions.manage_guild):
            await interaction.response.send_message('You no longer have permission to change this birthday.', ephemeral=True)
            return
        try:
            self.db.set_birthday(self.guild, self.user, int(self.day.value), int(self.month.value))
        except ValueError:
            await interaction.response.send_message('Enter a valid day and month, e.g. 25 and 12.', ephemeral=True)
            return
        await interaction.response.send_message('Birthday saved! Only day and month are stored. Server members can view it using /birthday list. Remove it with /birthday remove.', ephemeral=True)


class SetupView(discord.ui.View):
    def __init__(self, db, owner):
        super().__init__(timeout=180)
        self.db, self.owner = db, owner
        self.channel = self.mode = self.role = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner or not interaction.permissions.manage_guild:
            await interaction.response.send_message('Only the administrator who opened this menu can use it.', ephemeral=True)
            return False
        return True

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder='1. Announcement channel', row=0)
    async def channel_select(self, interaction, select):
        self.channel = select.values[0].id
        await interaction.response.defer()

    @discord.ui.select(placeholder='2. Who should be pinged?', options=[discord.SelectOption(label=label,value=value) for label,value in [('Birthday user','user'),('Selected role','role'),('User and role','both'),('Nobody','none')]], row=1)
    async def mode_select(self, interaction, select):
        self.mode = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder='3. Role (required for role/both)', row=2)
    async def role_select(self, interaction, select):
        self.role = select.values[0].id
        await interaction.response.defer()

    @discord.ui.button(label='Save configuration', style=discord.ButtonStyle.green, row=3)
    async def save(self, interaction, button):
        channel = interaction.guild.get_channel(self.channel) if self.channel else None
        error = None
        if not channel or not self.mode:
            error = 'Select an announcement channel and ping mode first.'
        elif not channel.permissions_for(interaction.guild.me).send_messages or not channel.permissions_for(interaction.guild.me).view_channel:
            error = 'Give the bot View Channel and Send Messages in that channel.'
        elif self.mode in ('role','both'):
            role = interaction.guild.get_role(self.role) if self.role else None
            if not role or role.is_default():
                error = 'Select a role other than @everyone.'
            elif not role.mentionable and not channel.permissions_for(interaction.guild.me).mention_everyone:
                error = 'Make the role mentionable or give the bot Mention Everyone in this channel.'
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        self.db.configure(interaction.guild_id,self.channel,self.mode,self.role)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f'Saved! Birthdays announced in <#{self.channel}> at 00:00 Malaysia time. Ping mode: {self.mode}.', view=self)
        self.stop()


@app_commands.guild_only()
class Birthdays(app_commands.Group, name='birthday', description='Server birthday calendar'):
    def __init__(self, db):
        super().__init__()
        self.db = db

    @app_commands.command(name='register', description='Register or update your day and month (visible to server members)')
    async def register(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BirthdayModal(self.db,interaction.guild_id,interaction.user.id))

    @app_commands.command(name='remove', description='Delete your birthday from this server')
    async def remove(self, interaction: discord.Interaction):
        self.db.remove(interaction.guild_id,interaction.user.id)
        await interaction.response.send_message('Your birthday was removed from this server.', ephemeral=True)

    async def show(self, interaction, page, upcoming):
        rows = self.db.birthdays(interaction.guild_id)
        today = datetime.now(MYT).date()
        if upcoming:
            rows = sorted(rows,key=lambda r: (next_birthday(r['day'],r['month'],today),r['user_id']))
        pages = max(1,(len(rows)+14)//15)
        if page > pages:
            await interaction.response.send_message(f'Choose a page between 1 and {pages}.',ephemeral=True)
            return
        lines = []
        for r in rows[(page-1)*15:page*15]:
            extra = f" — in {(next_birthday(r['day'],r['month'],today)-today).days} days" if upcoming else ''
            lines.append(f"<@{r['user_id']}> — {r['day']:02}/{r['month']:02}{extra}")
        await interaction.response.send_message(embed=discord.Embed(title=f"{'Upcoming birthdays' if upcoming else 'Server birthdays'} · {page}/{pages}",description='\n'.join(lines) or 'No birthdays registered yet.'),ephemeral=True,allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name='list', description='View all registered birthdays in this server')
    async def list_all(self, interaction: discord.Interaction, page: app_commands.Range[int,1,100000]=1):
        await self.show(interaction,page,False)

    @app_commands.command(name='upcoming', description='View birthdays sorted by next occurrence')
    async def upcoming(self, interaction: discord.Interaction, page: app_commands.Range[int,1,100000]=1):
        await self.show(interaction,page,True)

    @app_commands.command(name='setup', description='Admin: choose announcement channel and ping settings')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self, interaction: discord.Interaction):
        await interaction.response.send_message('Choose channel and ping mode, optionally select a role, then Save. Menu expires after 3 minutes.',view=SetupView(self.db,interaction.user.id),ephemeral=True)

    @app_commands.command(name='pause', description='Admin: pause announcements until setup is saved again')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def pause(self, interaction: discord.Interaction):
        self.db.pause(interaction.guild_id)
        await interaction.response.send_message('Announcements paused. Run /birthday setup to resume.',ephemeral=True)

    @app_commands.command(name='admin-set', description='Admin: register or update a member birthday')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def admin_set(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(BirthdayModal(self.db,interaction.guild_id,member.id))

    @app_commands.command(name='admin-remove', description='Admin: delete a member birthday')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def admin_remove(self, interaction: discord.Interaction, member: discord.Member):
        self.db.remove(interaction.guild_id,member.id)
        await interaction.response.send_message('Member birthday removed.',ephemeral=True)


class BirthdayBot(commands.Bot):
    def __init__(self, path):
        super().__init__(command_prefix=commands.when_mentioned,intents=discord.Intents.default(),allowed_mentions=discord.AllowedMentions.none())
        self.db = Database(path)
        self.scheduler = Scheduler(self.db,self.send_birthday,log)

    async def setup_hook(self):
        self.tree.add_command(Birthdays(self.db))
        self.tree.on_error = self.command_error
        await self.tree.sync()
        self.tick.start()

    async def command_error(self, interaction, error):
        message = 'You need Manage Server permission.' if isinstance(error,app_commands.MissingPermissions) else 'Something went wrong. Please try again or contact the bot administrator.'
        if not isinstance(error,app_commands.MissingPermissions):
            log.error('Command failed',exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send(message,ephemeral=True)
        else:
            await interaction.response.send_message(message,ephemeral=True)

    async def send_birthday(self, config, birthday, wish):
        guild = self.get_guild(config['guild_id'])
        if not guild:
            raise RuntimeError('Guild unavailable')
        try:
            member = await guild.fetch_member(birthday['user_id'])
        except discord.NotFound:
            self.db.remove(guild.id,birthday['user_id'])
            return
        channel = guild.get_channel(config['channel_id'])
        if not isinstance(channel,discord.TextChannel):
            raise RuntimeError('Announcement channel unavailable')
        mode = config['ping_mode']
        role = guild.get_role(config['role_id']) if config['role_id'] else None
        user_label = member.mention if mode in ('user','both') else discord.utils.escape_mentions(discord.utils.escape_markdown(member.display_name))
        prefix = f'{role.mention} ' if role and not role.is_default() and mode in ('role','both') else ''
        allowed = discord.AllowedMentions(everyone=False,users=[member] if mode in ('user','both') else False,roles=[role] if prefix else False,replied_user=False)
        await channel.send(prefix+wish.format(user=user_label),allowed_mentions=allowed)

    @tasks.loop(seconds=30)
    async def tick(self):
        try:
            await self.scheduler.run()
        except Exception:
            log.exception('Scheduler tick failed')

    @tick.before_loop
    async def before_tick(self):
        await self.wait_until_ready()

    async def close(self):
        self.tick.cancel()
        await super().close()
        self.db.close()


def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        raise SystemExit('Set DISCORD_TOKEN in the host environment before starting.')
    BirthdayBot(os.environ.get('DATABASE_PATH','data/birthdays.sqlite3')).run(token)

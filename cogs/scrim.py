import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.db import DB_PATH
from utils.constants import *
import aiosqlite
from datetime import datetime, timedelta
import json

class ScrimModal(discord.ui.Modal, title="Create a Scrim Request"):
    team1 = discord.ui.TextInput(label="Your Team Name", required=True)
    tier = discord.ui.TextInput(label="Tier (T1, T2, T3, PUBLIC)", required=True)
    maps = discord.ui.TextInput(label="Maps (comma-separated)", required=True)
    rounds = discord.ui.TextInput(label="Max Rounds (13 or 24)", required=True)
    format = discord.ui.TextInput(label="Format (BO1/BO2/BO3 or 1/2/3)", required=True)

    def __init__(self, bot, scrim_channel_id):
        super().__init__()
        self.bot = bot
        self.scrim_channel_id = scrim_channel_id

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📢 Scrim Request",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Team", value=self.team1.value)
        embed.add_field(name="Tier", value=self.tier.value)
        embed.add_field(name="Maps", value=self.maps.value)
        embed.add_field(name="Max Rounds", value=self.rounds.value)
        embed.add_field(name="Format", value=self.format.value)
        embed.set_footer(text="Scrim request expires in 24 hours.")

        view = ScrimButtons(self.bot, self.team1.value, interaction.user.id)

        channel = self.bot.get_channel(int(self.scrim_channel_id))
        if not channel:
            await interaction.response.send_message("Scrim posting channel not found.", ephemeral=True)
            return

        msg = await channel.send(embed=embed, view=view)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO scrims (message_id, channel_id, team, tier, maps, rounds, format, author_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(msg.id), str(channel.id), self.team1.value, self.tier.value,
                    self.maps.value, self.rounds.value, self.format.value,
                    str(interaction.user.id)
                )
            )
            await db.commit()

        await interaction.response.send_message("✅ Scrim request posted!", ephemeral=True)

class ScrimButtons(discord.ui.View):
    def __init__(self, bot, team, author_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.team = team
        self.author_id = author_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention} has accepted the scrim from **{self.team}**!", ephemeral=False)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention} has declined the scrim from **{self.team}**.", ephemeral=False)

    @discord.ui.button(label="Report", style=discord.ButtonStyle.secondary)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal(self.bot, interaction.message.id, interaction.channel.id))

    @discord.ui.button(label="Delete (Author)", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the author can delete this scrim request.", ephemeral=True)
            return
        await interaction.message.delete()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM scrims WHERE message_id = ?", (str(interaction.message.id),))
            await db.commit()
        await interaction.response.send_message("✅ Scrim request deleted.", ephemeral=True)

class ReportModal(discord.ui.Modal, title="Report Player or Team"):
    reason = discord.ui.TextInput(label="What happened?", style=discord.TextStyle.paragraph)

    def __init__(self, bot, msg_id, channel_id):
        super().__init__()
        self.bot = bot
        self.msg_id = msg_id
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        report_embed = discord.Embed(
            title="🚨 Scrim Report",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        report_embed.add_field(name="Reporter", value=interaction.user.mention)
        report_embed.add_field(name="Message ID", value=self.msg_id)
        report_embed.add_field(name="Channel ID", value=self.channel_id)
        report_embed.add_field(name="Reason", value=self.reason.value)

        report_channel = discord.utils.get(interaction.guild.text_channels, name=REPORTS_CHANNEL_NAME)
        if not report_channel:
            report_channel = await interaction.guild.create_text_channel(REPORTS_CHANNEL_NAME)

        await report_channel.send(embed=report_embed)
        await interaction.response.send_message("✅ Report submitted.", ephemeral=True)

class ScrimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.expire_scrims.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("📦 ScrimCog loaded.")

    @app_commands.command(name="scrim_create", description="Create a scrim request")
    async def scrim_create(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT scrim_create_channel_id, scrim_post_channel_id FROM config WHERE guild_id = ?", (str(interaction.guild.id),))
            row = await cursor.fetchone()
        if not row:
            return await interaction.response.send_message("❌ Setup incomplete. Use /setup to configure channels.", ephemeral=True)

        create_channel_id, post_channel_id = row
        if str(interaction.channel.id) != str(create_channel_id):
            return await interaction.response.send_message("❌ Use this command only in the scrim creation channel.", ephemeral=True)

        await interaction.response.send_modal(ScrimModal(self.bot, post_channel_id))

    @tasks.loop(minutes=1)
    async def expire_scrims(self):
        now = datetime.utcnow()
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT message_id, channel_id, created_at FROM scrims")
            rows = await cursor.fetchall()

            for message_id, channel_id, created_at in rows:
                created_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                if now - created_dt > timedelta(hours=24):
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        try:
                            msg = await channel.fetch_message(int(message_id))
                            await msg.delete()
                        except:
                            pass
                    await db.execute("DELETE FROM scrims WHERE message_id = ?", (message_id,))
            await db.commit()

async def setup(bot):
    await bot.add_cog(ScrimCog(bot))

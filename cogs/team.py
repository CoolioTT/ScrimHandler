import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from utils.db import DB_PATH
from utils.constants import TEAM_ROLES, TEAM_REGISTER_CHANNEL_NAME

class TeamModal(discord.ui.Modal, title="Register Your Team"):
    team_name = discord.ui.TextInput(label="Team Name", required=True)
    manager = discord.ui.TextInput(label="Manager (mention)", required=True)
    ceo = discord.ui.TextInput(label="CEO (mention)", required=True)
    captain = discord.ui.TextInput(label="Team Captain (mention)", required=True)
    players = discord.ui.TextInput(label="Players (mention multiple)", required=True)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        team_role = discord.utils.get(guild.roles, name=self.team_name.value)

        if team_role:
            await interaction.response.send_message("⚠️ A team with that name already exists.", ephemeral=True)
            return

        team_role = await guild.create_role(name=self.team_name.value)

        members = {
            "Manager": self.manager.value,
            "CEO": self.ceo.value,
            "Captain": self.captain.value,
            "Player": self.players.value
        }

        for role_label, user_mentions in members.items():
            mentions = user_mentions.split()
            for mention in mentions:
                try:
                    member_id = int(mention.strip('<@!>'))
                    member = guild.get_member(member_id)
                    if member:
                        await member.add_roles(team_role)
                        await member.edit(nick=f"{member.display_name} || {role_label}")
                except:
                    continue

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO teams (guild_id, team_name, manager, ceo, captain, players) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    str(guild.id), self.team_name.value,
                    self.manager.value, self.ceo.value,
                    self.captain.value, self.players.value
                )
            )
            await db.commit()

        await interaction.response.send_message(f"✅ Team **{self.team_name.value}** registered successfully!", ephemeral=True)

class TeamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name=TEAM_REGISTER_CHANNEL_NAME)
        if not channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member.guild.me: discord.PermissionOverwrite(read_messages=True),
            }
            channel = await member.guild.create_text_channel(TEAM_REGISTER_CHANNEL_NAME, overwrites=overwrites)
        try:
            await channel.send(f"👋 Welcome {member.mention}! Please register your team using `/team register`.")
        except:
            pass

    @app_commands.command(name="team_register", description="Register your team")
    async def team_register(self, interaction: discord.Interaction):
        channel = discord.utils.get(interaction.guild.text_channels, name=TEAM_REGISTER_CHANNEL_NAME)
        if interaction.channel != channel:
            return await interaction.response.send_message("❌ Please use this in the team registration channel.", ephemeral=True)
        await interaction.response.send_modal(TeamModal(self.bot))

async def setup(bot):
    await bot.add_cog(TeamCog(bot))

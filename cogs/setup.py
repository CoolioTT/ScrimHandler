import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from utils.db import DB_PATH
from utils.constants import DEFAULT_TIERS

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_admin(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="setup", description="Start interactive bot setup.")
    @app_commands.check(is_admin)
    async def setup_wizard(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔧 Use the following commands to configure:\n"
                                                "`/set_scrim_channel`, `/set_team_channel`, `/init_tiers`, `/set_ip`, `/reset_db`", ephemeral=True)

    @app_commands.command(name="set_scrim_channel", description="Set the channel where scrim requests are posted.")
    @app_commands.check(is_admin)
    async def set_scrim_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
                             (str(interaction.guild_id), "scrim_channel", str(channel.id)))
            await db.commit()
        await interaction.response.send_message(f"✅ Scrim post channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="set_team_channel", description="Set the channel for team registration.")
    @app_commands.check(is_admin)
    async def set_team_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
                             (str(interaction.guild_id), "team_register_channel", str(channel.id)))
            await db.commit()
        await interaction.response.send_message(f"✅ Team registration channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="init_tiers", description="Create default tier roles (T1, T2, T3, PUBLIC)")
    @app_commands.check(is_admin)
    async def init_tiers(self, interaction: discord.Interaction):
        guild = interaction.guild
        created_roles = []
        for tier in DEFAULT_TIERS:
            role = discord.utils.get(guild.roles, name=tier)
            if not role:
                new_role = await guild.create_role(name=tier)
                created_roles.append(new_role.name)
        if created_roles:
            await interaction.response.send_message(f"✅ Created roles: {', '.join(created_roles)}", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ All tier roles already exist.", ephemeral=True)

    @app_commands.command(name="set_ip", description="Set allowed IP for web dashboard access.")
    @app_commands.check(is_admin)
    async def set_ip(self, interaction: discord.Interaction, ip_address: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)",
                             (str(interaction.guild_id), "dashboard_ip", ip_address))
            await db.commit()
        await interaction.response.send_message(f"✅ IP address for dashboard set to `{ip_address}`", ephemeral=True)

    @app_commands.command(name="reset_db", description="Reset the entire database.")
    @app_commands.check(is_admin)
    async def reset_db(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ Are you sure? Type `confirm` within 30 seconds to wipe the DB.", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.content.lower() == "confirm"

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)
        except:
            return await interaction.followup.send("❌ Timeout. DB reset cancelled.", ephemeral=True)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM config")
            await db.execute("DELETE FROM teams")
            await db.execute("DELETE FROM scrims")
            await db.commit()

        await interaction.followup.send("✅ Database wiped successfully.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetupCog(bot))

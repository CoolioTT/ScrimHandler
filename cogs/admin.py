import discord
from discord.ext import commands
from discord import app_commands
import json
import sqlite3


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin Cog Loaded.")

    @app_commands.command(name="setup", description="Admin setup for team registration and scrim channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction,
                    reg_channel: discord.TextChannel,
                    scrim_channel: discord.TextChannel,
                    allowed_ip: str):
        config = {
            "registration_channel_id": reg_channel.id,
            "scrim_post_channel_id": scrim_channel.id,
            "allowed_dashboard_ip": allowed_ip
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        await interaction.response.send_message("✅ Setup saved!", ephemeral=True)

    @app_commands.command(name="reset_db", description="Reset scrim/team database")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_db(self, interaction: discord.Interaction):
        db = sqlite3.connect("scrim.db")
        db.execute("DROP TABLE IF EXISTS scrims")
        db.execute("DROP TABLE IF EXISTS teams")
        db.commit()
        db.close()
        await interaction.response.send_message("🗑️ Database reset!", ephemeral=True)




async def setup(bot):
    await bot.add_cog(AdminCog(bot))

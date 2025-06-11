import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from utils.db import DB_PATH

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="scrim_stats", description="View your team's scrim stats")
    async def scrim_stats(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT team_name FROM teams WHERE user_id = ?", (str(user_id),)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return await interaction.response.send_message("❌ You are not part of a registered team.", ephemeral=True)
                team_name = row[0]

            async with db.execute("SELECT COUNT(*) FROM scrims WHERE team1 = ? OR team2 = ?", (team_name, team_name)) as cursor:
                total = await cursor.fetchone()

        embed = discord.Embed(title=f"📊 Scrim Stats for {team_name}", color=discord.Color.green())
        embed.add_field(name="Total Scrims", value=total[0])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="team_view", description="View a team’s info and roster")
    @app_commands.describe(team_name="Exact name of the team you want to view")
    async def team_view(self, interaction: discord.Interaction, team_name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, role FROM teams WHERE team_name = ?", (team_name,)) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        members = []
        for user_id, role in rows:
            user = interaction.guild.get_member(int(user_id))
            if user:
                members.append(f"{user.mention} - `{role}`")
            else:
                members.append(f"<@{user_id}> - `{role}` (Not Found)")

        embed = discord.Embed(title=f"🏷️ Team Info: {team_name}", color=discord.Color.blue())
        embed.add_field(name="Roster", value="\n".join(members), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))

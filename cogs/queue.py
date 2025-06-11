import discord
from discord.ext import commands
from discord import app_commands
from utils.db import DB_PATH
import aiosqlite
from datetime import datetime, timedelta

class QueueClaimView(discord.ui.View):
    def __init__(self, post_id):
        super().__init__(timeout=None)
        self.post_id = post_id

    @discord.ui.button(label="✅ Claim", style=discord.ButtonStyle.success, custom_id="queue_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT claimed_by FROM queue WHERE id = ?", (self.post_id,)) as cursor:
                row = await cursor.fetchone()

            if row and row[0]:
                return await interaction.response.send_message("⚠️ Already claimed by someone else.", ephemeral=True)

            await db.execute("UPDATE queue SET claimed_by = ?, claimed_at = ? WHERE id = ?",
                             (str(interaction.user.id), datetime.utcnow().isoformat(), self.post_id))
            await db.commit()

        await interaction.response.send_message("🎉 You claimed the scrim!", ephemeral=True)

    @discord.ui.button(label="❌ Unclaim", style=discord.ButtonStyle.danger, custom_id="queue_unclaim")
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT claimed_by FROM queue WHERE id = ?", (self.post_id,)) as cursor:
                row = await cursor.fetchone()

            if not row or row[0] != str(interaction.user.id):
                return await interaction.response.send_message("❌ You didn’t claim this post.", ephemeral=True)

            await db.execute("UPDATE queue SET claimed_by = NULL, claimed_at = NULL WHERE id = ?",
                             (self.post_id,))
            await db.commit()

        await interaction.response.send_message("✅ You unclaimed the scrim.", ephemeral=True)

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="scrim_queue", description="Post your team as LFS (Looking For Scrim)")
    @app_commands.describe(tier="Your team's tier", message="Extra details like time, region, etc.")
    async def scrim_queue(self, interaction: discord.Interaction, tier: str, message: str):
        embed = discord.Embed(
            title="🕹️ Looking For Scrim",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Team", value=interaction.user.mention)
        embed.add_field(name="Tier", value=tier)
        embed.add_field(name="Details", value=message)
        embed.set_footer(text="Click a button to claim or unclaim.")

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO queue (user_id, message, tier, created_at) VALUES (?, ?, ?, ?)",
                             (str(interaction.user.id), message, tier, datetime.utcnow().isoformat()))
            await db.commit()
            cursor = await db.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            post_id = row[0]

        view = QueueClaimView(post_id=post_id)
        await interaction.response.send_message(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(QueueClaimView(post_id=0))  # Init persistent view

async def setup(bot):
    await bot.add_cog(QueueCog(bot))

import discord
from discord.ext import commands
import config
import json
import os
from datetime import datetime

SCRIM_DB_FILE = "data/scrim_requests.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(SCRIM_DB_FILE):
    with open(SCRIM_DB_FILE, "w") as f:
        json.dump({}, f)

def save_scrim_entry(message_id, data):
    with open(SCRIM_DB_FILE, "r+") as f:
        db = json.load(f)
        db[str(message_id)] = data
        f.seek(0)
        json.dump(db, f, indent=4)
        f.truncate()

def delete_scrim_entry(message_id):
    with open(SCRIM_DB_FILE, "r+") as f:
        db = json.load(f)
        db.pop(str(message_id), None)
        f.seek(0)
        json.dump(db, f, indent=4)
        f.truncate()

class ScrimRequestModal(discord.ui.Modal, title="Scrim Request Form"):
    tier = discord.ui.TextInput(label="Tier", placeholder="e.g. Tier 3")
    games = discord.ui.TextInput(label="Games", placeholder="e.g. 2")
    datetime = discord.ui.TextInput(label="Date/Time", placeholder="e.g. 06/11 8PM SGT")
    servers = discord.ui.TextInput(label="Servers", placeholder="e.g. SG, HK")

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📌 Scrim Request", color=discord.Color.purple())
        embed.add_field(name="Tier", value=self.tier.value, inline=True)
        embed.add_field(name="Games", value=self.games.value, inline=True)
        embed.add_field(name="Time", value=self.datetime.value, inline=False)
        embed.add_field(name="Servers", value=self.servers.value, inline=True)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        channel = interaction.client.get_channel(config.SCRIM_BOARD_CHANNEL_ID)
        message = await channel.send(embed=embed, view=DeleteScrimButton())

        save_scrim_entry(message.id, {
            "user_id": interaction.user.id,
            "tier": self.tier.value,
            "games": self.games.value,
            "datetime": self.datetime.value,
            "servers": self.servers.value,
            "timestamp": datetime.utcnow().isoformat()
        })

        await interaction.response.send_message("✅ Posted your scrim!", ephemeral=True)

class DeleteScrimButton(discord.ui.View):
    @discord.ui.button(label="Delete Scrim", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        with open(SCRIM_DB_FILE, "r") as f:
            db = json.load(f)
        data = db.get(str(message.id))

        if data and data["user_id"] == interaction.user.id:
            delete_scrim_entry(message.id)
            await message.delete()
            await interaction.response.send_message("🗑️ Scrim deleted!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ You can't delete this.", ephemeral=True)

class ScrimCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setup_scrim(self, ctx):
        """Sends the request scrim button"""
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Request Scrim", style=discord.ButtonStyle.primary, custom_id="scrim_button"))
        await ctx.send("Click below to request a scrim:", view=ScrimButtonView())

class ScrimButtonView(discord.ui.View):
    @discord.ui.button(label="Request Scrim", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ScrimRequestModal())

async def setup(bot):
    await bot.add_cog(ScrimCog(bot))

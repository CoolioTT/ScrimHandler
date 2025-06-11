import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from utils.db import DB_PATH

class ReportView(discord.ui.View):
    def __init__(self, scrim_id):
        super().__init__(timeout=None)
        self.scrim_id = scrim_id

    @discord.ui.button(label="📣 Report Team/Player", style=discord.ButtonStyle.danger, custom_id="report_button")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal(self.scrim_id))

class ReportModal(discord.ui.Modal, title="Report Team or Player"):
    reason = discord.ui.TextInput(label="Reason for Report", style=discord.TextStyle.paragraph, required=True, max_length=1000)

    def __init__(self, scrim_id):
        super().__init__()
        self.scrim_id = scrim_id

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        reporter = interaction.user

        # Ensure report channel exists
        report_channel = discord.utils.get(guild.text_channels, name="scrim-reports")
        if not report_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
            }
            report_channel = await guild.create_text_channel("scrim-reports", overwrites=overwrites)

        embed = discord.Embed(title="⚠️ Scrim Report Submitted", color=discord.Color.red())
        embed.add_field(name="Scrim ID", value=self.scrim_id, inline=False)
        embed.add_field(name="Reporter", value=reporter.mention, inline=True)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.set_footer(text="Staff, please review this report.")

        await report_channel.send(embed=embed)
        await interaction.response.send_message("✅ Report submitted to moderators.", ephemeral=True)

class ReportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ReportView(scrim_id=0))  # Dummy init for persistent view registration

async def setup(bot):
    await bot.add_cog(ReportCog(bot))

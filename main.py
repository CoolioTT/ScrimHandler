import discord
from discord.ext import commands
from utils.db import init_db
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await init_db()
    await bot.tree.sync()
    print("✅ Slash commands synced.")

async def main():
    async with bot:
        from bot import load_cogs
        await load_cogs(bot)
        await bot.start("YOUR_DISCORD_BOT_TOKEN")

asyncio.run(main())

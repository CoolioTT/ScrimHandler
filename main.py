from bot import bot, load_cogs
import config

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def main():
    await load_cogs()
    await bot.start(config.TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

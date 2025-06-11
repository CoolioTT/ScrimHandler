async def load_cogs(bot):
    await bot.load_extension("cogs.scrim")
    await bot.load_extension("cogs.team")
    await bot.load_extension("cogs.setup")
    await bot.load_extension("cogs.stats")

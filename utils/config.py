import aiosqlite
from utils.db import DB_PATH

async def get_config(guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                guild_id TEXT PRIMARY KEY,
                scrim_channel_id TEXT,
                register_channel_id TEXT
            )
        """)
        async with db.execute("SELECT scrim_channel_id, register_channel_id FROM config WHERE guild_id = ?", (str(guild_id),)) as cursor:
            row = await cursor.fetchone()
            return row

async def set_config(guild_id, scrim_channel_id=None, register_channel_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO config (guild_id, scrim_channel_id, register_channel_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                scrim_channel_id = COALESCE(?, scrim_channel_id),
                register_channel_id = COALESCE(?, register_channel_id)
        """, (str(guild_id), scrim_channel_id, register_channel_id, scrim_channel_id, register_channel_id))
        await db.commit()

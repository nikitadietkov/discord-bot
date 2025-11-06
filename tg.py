import asyncio
from telethon import TelegramClient, events
import discord
from discord.ext import commands
import io
import mimetypes
import re

api_id = 29093027
api_hash = 'e9a91f1cddbea153bfb7015ef6918ca8'
channel_username = 'ddnepr_vse'
DISCORD_TOKEN = 'MTQzNjA4NTgwOTI2MTMxNDA4OA.GuSTez.RfmOx8gIoy0N-KcgGXHuhbK9wLtRTnQJk8C7kE'
DISCORD_CHANNEL_ID = 1436106038708277268

TRIGGER_WORDS = ["дтек", "дніпропетровщина", "графік", "графіки", "світло", "ремонт", "відключення"]

tg_client = TelegramClient('session_name', api_id, api_hash)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

processed_message_ids = set()
processed_group_ids = set()
processing_lock = asyncio.Lock()

def disable_link_previews(text: str) -> str:
    return re.sub(r'(https?://\S+)', r'<\1>', text)

def has_trigger_word(text: str) -> bool:
    """Проверяет наличие хотя бы одного слова-триггера в тексте"""
    if not text:
        return False
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in TRIGGER_WORDS)

async def send_files_to_discord(files, caption=None):
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return
    await channel.send(content=caption or "", files=files)

def _make_filename(m, default_prefix="media"):
    filename = (getattr(m.file, "name", None) or f"{default_prefix}_{m.id}")
    mime_type = getattr(m.file, "mime_type", None) if m.file else None
    ext = None
    if mime_type:
        ext = mimetypes.guess_extension(mime_type)
    if not ext:
        if "video" in (mime_type or ""):
            ext = ".mp4"
        elif "image" in (mime_type or ""):
            ext = ".jpg"
        else:
            ext = ".bin"
    if not filename.endswith(ext):
        filename += ext
    return filename

@tg_client.on(events.NewMessage(chats=channel_username))
async def handler(event):
    message = event.message

    async with processing_lock:
        if message.id in processed_message_ids:
            return

        gid = getattr(message, 'grouped_id', None)
        if gid:
            if gid in processed_group_ids:
                processed_message_ids.add(message.id)
                return

            recent = await tg_client.get_messages(channel_username, limit=50)
            group_msgs = [m for m in reversed(recent) if getattr(m, 'grouped_id', None) == gid]

            if not group_msgs:
                group_msgs = [message]

            processed_group_ids.add(gid)
            for m in group_msgs:
                processed_message_ids.add(m.id)

            discord_files = []
            caption = None
            for m in group_msgs:
                if not caption and (getattr(m, "text", None) or getattr(m, "message", None)):
                    caption = m.text or m.message
                    caption = disable_link_previews(caption)

            if not has_trigger_word(caption):
                return

            for m in group_msgs:
                if m.media:
                    file_bytes = await m.download_media(bytes)
                    filename = _make_filename(m)
                    discord_files.append(discord.File(io.BytesIO(file_bytes), filename=filename))

            if discord_files:
                await send_files_to_discord(discord_files, caption=caption)
            elif caption:
                await send_files_to_discord([], caption=caption)

        else:
            processed_message_ids.add(message.id)

            if not has_trigger_word(message.text):
                return

            if message.text and not message.media:
                text = disable_link_previews(message.text)
                await send_files_to_discord([], caption=text)
                return

            if message.media:
                file_bytes = await message.download_media(bytes)
                filename = _make_filename(message)
                discord_file = discord.File(io.BytesIO(file_bytes), filename=filename)

                caption = message.text or ""
                caption = disable_link_previews(caption)
                await send_files_to_discord([discord_file], caption=caption)

@bot.event
async def on_ready():
    print(f"✅ Discord бот вошёл как {bot.user}")

async def main():
    await asyncio.gather(
        tg_client.start(),
        bot.start(DISCORD_TOKEN)
    )

asyncio.run(main())

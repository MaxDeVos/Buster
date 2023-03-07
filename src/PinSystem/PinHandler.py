import asyncio
import io
import os

import aiohttp
import discord
import sched
import time

import src.PinSystem.HistoryManager
from src.TimestampGenerator import TimestampGenerator

s = sched.scheduler(time.time, time.sleep)
ts = TimestampGenerator("PINS")


class PinHandler:

    guild: discord.Guild
    pin_channel: discord.TextChannel

    def __init__(self, channel, guild):
        self.pin_threshold = int(os.environ.get("PIN_THRESHOLD"))
        self.pin_channel = channel
        self.guild = guild
        self.pins_ready = False
        self.pinned_messages = []
        asyncio.get_event_loop().create_task(self.get_pin_history())

    async def get_pin_history(self):
        async for message in self.pin_channel.history(limit=None, oldest_first=True):
            if message.author.bot:
                try:
                    self.pinned_messages.append(int(message.content.split("\n")[0].split("/")[6]))
                except:
                    # logging.info("ERROR", getTimeStamp(), "Failed to load previous pin: ", message)
                    pass
        self.pins_ready = True
        # await self.comb_for_missed_pins()
        ts.info("Completed Collecting Pin History")
        ts.info("Successfully Started Pin Manager")

    async def pin(self, message, force=False):
        if not self.pins_ready and not force:
            ts.error("Attempted to pin before PinHandler was ready. You'll have to try again")
        else:
            ts.info(f"Pinning Message From: {message.author.mention}")
            self.pinned_messages.append(message.id)

            files = []
            for attachment in message.attachments:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            ts.error("Couldn't download file")
                        data = io.BytesIO(await resp.read())
                        files.append(discord.File(data, attachment.filename))

            out = str(message.jump_url) + "\n" + "**Author:** " + message.author.mention + \
                  "  |  " + "**Channel:** " + message.channel.mention + "\n" + message.clean_content

            await self.pin_channel.send(out, files=files)

    async def handlePinReaction(self, reaction, client):
        channel = client.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if not self.pinned_messages.__contains__(message.id):
            for reaction in message.reactions:
                if reaction.emoji == "📌":
                    if reaction.count >= self.pin_threshold:
                        await self.pin(message)

    def filterOutPinned(self, message):
        return message.id not in self.pinned_messages

    async def comb_for_missed_pins(self):
        to_pin = []
        for channel in await self.guild.fetch_channels():
            try:
                for message in await src.PinSystem.HistoryManager.get_posts_above_reaction_threshold_channel(channel, self.pinned_messages, 6):
                    to_pin.append(message)
                ts.info(f"Combed Through {channel.name}")
            except AttributeError:
                pass
            except discord.errors.Forbidden:
                pass
        to_pin = filter(self.filterOutPinned, to_pin)
        to_pin = sorted(to_pin, key=lambda x: x.created_at.timestamp())
        for m in to_pin:
            await self.pin(m)
            time.sleep(.05)


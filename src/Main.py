import logging
import os
import random
import sys
from abc import ABC

import discord
from discord import TextChannel, Guild
from discord.ext import commands

from src.DatabaseCog.DatabaseCog import DatabaseCog
from src.EmojiCog.EmojiAnnouncerCog import EmojiAnnouncerCog

sys.path.insert(1, '')  # if this isn't here, local imports fail in Docker. ¯\_(ツ)_/¯

from src.PinSystem.PinCog import PinCog
from src.TimestampGenerator import TimestampGenerator
from src.Translation.TranslationCog import TranslationCog
from src.RoleManager.RoleManagerCog import RoleManagerCog
from src.InviteManager.InviteCog import InviteCog

ts = TimestampGenerator("BSTR")
active_guild_id = int(os.environ.get("GUILD_ID"))


class Bot(commands.Bot, ABC):

    channelDict: dict[str, TextChannel]
    guild: Guild

    def __init__(self, *args, **kwargs):
        self.guild = None
        self.channelDict = {}
        super().__init__(*args, **kwargs)

    async def on_ready(self):

        # Find guild that matches active_guild_id
        for guild in self.guilds:
            if guild.id == active_guild_id:
                self.guild = guild
                ts.info(f"Found Guild: {guild.name}")
                break

        # Populate channelDict for future convenience
        for a in self.guild.text_channels:
            self.channelDict[a.name] = a

        # Send Message
        # ch = await self.fetch_channel(852322660125114398)
        # await ch.send("I'm back, asswipes")

        # Add reaction
        # ch = await self.fetch_channel(852322660125114398)
        # msg = await ch.fetch_message(959300803972190259)
        # await msg.add_reaction("🟠")

    async def determine_guild_users(self):
        """
        :return: number of non-bot users in self.bot.guild
        """
        total_users = 0
        async for member in self.bot.guild.fetch_members():
            if not member.bot:
                total_users += 1
        return total_users

    async def query_database(self, table_name, row=None, col=None):
        """
        Fires on_query_database event in DatabaseCog
        which then fires on_query_response and is picked up here
        See the pydoc @ DatabaseCog/DatabaseCog.py for details
        :param str table_name:
        :param str row:
        :param int col:
        :return: Any
        """
        query_id = random.randrange(10000000, 99999999)
        self.dispatch("query_database", query_id, table_name)

        while True:
            result = await self.wait_for("query_response")
            if int(result[0]) == query_id:
                out = result[1]
                if row is None:
                    if col is None:
                        return out
                    return out[row]
                return out[row][col]


# Create and start Buster
bot = Bot(intents=discord.Intents.all())

# Load cogs into Buster
ts.info("Starting Cogs")
bot.add_cog(DatabaseCog(bot))
bot.add_cog(PinCog(bot))
bot.add_cog(TranslationCog(bot))
bot.add_cog(RoleManagerCog(bot))
bot.add_cog(InviteCog(bot))
bot.add_cog(EmojiAnnouncerCog(bot))

bot.run(os.environ.get('APIKEY'))

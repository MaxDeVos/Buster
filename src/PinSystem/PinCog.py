import discord
from discord.ext import commands

from src.PinSystem.PinHandler import PinHandler
from src.TimestampGenerator import TimestampGenerator

ts = TimestampGenerator("PINS")


class PinCog(commands.Cog):
    guild: discord.Guild

    def __init__(self, bot):
        self.bot = bot
        self.pinHandler = None
        ts.info("Created Pin Manager")

    @commands.Cog.listener()
    async def on_ready(self):
        self.pinHandler = PinHandler(self.bot.channelDict["pins"], self.bot.guild)
        ts.info("Started Pin Manager")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.guild_id == self.bot.guild.id:
            await self.pinHandler.handlePinReaction(reaction, self.bot)

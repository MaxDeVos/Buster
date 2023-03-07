import os
from typing import Sequence

import discord
from discord.ext import commands

from src.EmojiCog.Image import Image
from src.TimestampGenerator import TimestampGenerator

ts = TimestampGenerator("EMOJ")


class EmojiCog(commands.Cog):
    guild: discord.Guild

    def __init__(self, bot):
        self.bot = bot
        self.image_processor = None
        ts.info("Created Emoji Manager")

    @commands.Cog.listener()
    async def on_ready(self):
        ts.info("Started Emoji Manager")

    @commands.slash_command(guild_ids=[int(os.environ.get("GUILD_ID"))])
    async def upload_emoji(self, interaction: discord.Interaction, emoji_name: str, file: discord.Attachment):
        self.image_processor = Image(file, emoji_name)
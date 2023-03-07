import io
import os
import time
from typing import Sequence

import discord
from discord import Emoji, File, Guild, AuditLogEntry, Member
from discord.ext import commands

from src.EmojiCog.Image import Image
from src.TimestampGenerator import TimestampGenerator

ts = TimestampGenerator("EMOJ")


class EmojiAnnouncerCog(commands.Cog):
    guild: discord.Guild

    def __init__(self, bot):
        self.bot = bot
        self.image_processor = None
        ts.info("Created Emoji Manager")

    @commands.Cog.listener()
    async def on_ready(self):
        ts.info("Started Emoji Manager")

    # @commands.slash_command(guild_ids=[int(os.environ.get("GUILD_ID"))])
    # async def upload_emoji(self, interaction: discord.Interaction, emoji_name: str, file: discord.Attachment):
    #     self.image_processor = Image(file, emoji_name)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: Guild, before: Sequence[Emoji], after: Sequence[Emoji]):

        changed_emoji: Emoji

        audit_log_events = guild.audit_logs(limit=1)
        audit_log_entry: AuditLogEntry
        async for entry in audit_log_events:
            audit_log_entry = entry

        # noinspection PyUnboundLocalVariable
        user: Member = audit_log_entry.user

        change_type = "removed"
        suffix = "ed"
        if len(before) < len(after):
            change_type = "added"
            suffix = "s"
            changed_emoji = self.determine_new_emoji(before, after)
        elif len(before) > len(after):
            changed_emoji = self.determine_new_emoji(after, before)
        else:
            name_before = audit_log_entry.changes.before.name
            name_after = audit_log_entry.changes.after.name

            changed_emoji = discord.utils.find(lambda m: m.name == name_after, guild.emojis)
            image_bytes = await changed_emoji.read()

            await self.bot.channelDict["server-announcements"].send(f"**EMOJI UPDATE**"
                                                                    f"\n{user.mention} has changed the name of "
                                                                    f"**:{name_before}:** to **:{name_after}:**",
                                                                    file=File(fp=io.BytesIO(image_bytes),
                                                                              filename=f"{changed_emoji.name}.png"))
            return

        image_bytes = await changed_emoji.read()

        await self.bot.channelDict["server-announcements"].send(f"**EMOJI UPDATE**"
                                                                f"\n{user.mention} has {change_type} **:{changed_emoji.name}:**"
                                                                f"\nHere's what that bad boy look{suffix} like",
                                                                file=File(fp=io.BytesIO(image_bytes),
                                                                          filename=f"{changed_emoji.name}.png"))

    def determine_new_emoji(self, _before: Sequence[Emoji], _after: Sequence[Emoji]) -> Emoji:
        before = {}
        for emoji in _before:
            before[emoji.id] = emoji

        after = {}
        for emoji in _after:
            after[emoji.id] = emoji

        different_key = after.keys() - before.keys()
        return after[different_key.pop()]

    async def on_emoji_add(self, emoji, user):
        pass

    async def on_emoji_delete(self, emoji, user):
        pass

    async def on_emoji_change(self, emoji, user):
        pass
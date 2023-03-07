import os

import discord
from discord import Cog, ApplicationContext
from discord.ext import commands

from src.DatabaseCog.DatabaseModel import DatabaseModel
from src.TimestampGenerator import TimestampGenerator

ts = TimestampGenerator("DATA")


def sanitize_input(input_text):
    """
    Takes a string and replaces any commas with periods for safe CSV-style storage.
    :param input_text: original string to store
    :return: string with all commas replaced as periods
    """
    return input_text.replace(",", ".")


class DatabaseCog(Cog):
    """
    This Cog allows for using one TextChannel as an event-driven database. This has the benefit of allowing the bot's
        code to be entirely portable, all data ABOUT the server is stored IN the server. No CVS files or mysql dbs.
        Server goes down? Fire it up on your laptop.
        The events are as follows, and can be fired from asynchronous setting with bot.dispatch("name_of_event") or
        listened for by creating a listener function with the name on_name_of_event(), just like native Discord events.

    The easiest way to query information from the database is through the query_database() function in Bot (Main.py).
        Writing to the database is done through the following events:

    database_query_add_row(table_name, new_row, suspend_rewrite=False)
    database_query_remove(table_name, row_id)
    on_database_query_change(table_name, row_id, col, new_val):
    on_database_query_replace_row(table_name, row_id, new_row, suspend_rewrite=False)

    Suspend rewrite means that the database will not update the messages until another query (lacking suspend_rewrite)
        tells them to. This is useful for large blocks of updates, and keeps the event queue from bogging down with
        message edits.

    This "API" also includes support for directly changing the database contents within Discord. To do this, reply to
        the table you want to update with the new contents. It will copy your message verbatim, so be careful. To listen
        for this, listen for "on_manual_database_update".

    I recommend using the "interface" TableEntries to create a model of your data entries, since the pure database
        is rather crude. See InviteManager/VoteModel.py for a extensively implemented example of this. For an example
        of implementing this entire system, see InviteManager/InviteCog.py, which is fully documented.

    """
    tables: dict[str, DatabaseModel]
    tableTitles: dict[int, str]

    def __init__(self, bot):
        self.bot = bot
        self.tables = {}
        self.tableTitles = {}
        ts.info("Created Database Cog")

    @commands.Cog.listener()
    async def on_query_database(self, query_id, table_name, row=None, col=None):
        table = table_name
        output = None
        try:
            if col is None:
                if row is None:
                    output = self.tables[table].data
                else:
                    output = self.tables[table].data[row]
            else:
                output = self.tables[table].data[row][col]
        except Exception as e:
            pass

        self.bot.dispatch("query_response", query_id, output)

    @commands.Cog.listener()
    async def on_database_query_add_row(self, table_name, new_row, suspend_rewrite=False):
        await self.tables[table_name].add_row(new_row, suspend_rewrite=suspend_rewrite)

    @commands.Cog.listener()
    async def on_database_query_remove(self, table_name, row_id):
        await self.tables[table_name].remove_row(row_id)

    @commands.Cog.listener()
    async def on_database_query_change(self, table_name, row_id, col, new_val):
        if type(new_val) is str:
            await self.tables[table_name].update_entry(row_id, col, sanitize_input(new_val))
        else:
            await self.tables[table_name].update_entry(row_id, col, new_val)

    @commands.Cog.listener()
    async def on_database_query_replace_row(self, table_name, row_id, new_row, suspend_rewrite=False):
        await self.tables[table_name].remove_row(row_id, True)
        await self.tables[table_name].add_row(new_row, suspend_rewrite)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.read_tables_from_database()
        ts.info("Database Ready")
        self.bot.dispatch("database_ready")

    async def read_tables_from_database(self):
        bot_channel: discord.TextChannel = self.bot.channelDict["bot-database"]
        async for message in bot_channel.history(oldest_first=True):
            if not message.author.bot:
                continue
            table_title = message.content.split("\n")[0]
            self.tables[table_title] = DatabaseModel(self.bot, message)
            self.tableTitles[message.id] = table_title
            ts.info(f"Registered database model {table_title} with link to message {message.id}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == 155102908281520129 and message.reference is not None and \
                message.reference.message_id in self.tableTitles:
            table_title = self.tableTitles[message.reference.message_id]
            await self.tables[table_title].message.edit(content=message.content)
            await message.delete()
            await self.read_tables_from_database()
            self.tables[table_title].reload()
            self.bot.dispatch("manual_database_update", self.tableTitles[message.reference.message_id],
                              self.tables[self.tableTitles[message.reference.message_id]], message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, data: discord.RawMessageUpdateEvent):
        if data.message_id in self.tableTitles:
            ts.info(f"Updated {self.tableTitles[data.message_id]}")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.channel_id == self.bot.channelDict["bot-database"]:
            if payload.message_id in self.tableTitles:
                del self.tables[self.tableTitles[payload.message_id]]
                del self.tableTitles[payload.message_id]

    @commands.slash_command(guild_ids=[int(os.environ.get("GUILD_ID"))])
    async def generate_database_message(self, ctx: ApplicationContext, arg1):
        res = await ctx.send(arg1 + "\nID,")
        self.tables[arg1] = DatabaseModel(self.bot, res)
        self.tableTitles[res.id] = arg1
        await ctx.response.send_message("done", ephemeral=True)

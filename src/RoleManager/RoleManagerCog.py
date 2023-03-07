import asyncio

import discord
from discord.ext import commands

from src.RoleManager.RoleButton import RoleButton
from src.TimestampGenerator import TimestampGenerator

ts = TimestampGenerator("ROLE")


class RoleManagerCog(commands.Cog):
    guild: discord.Guild

    def __init__(self, bot):
        self.bot = bot
        print(ts.get_time_stamp(), "Created Role Manager")

        self.pronounDict = []
        self.gamesDict = []
        self.locationDict = []
        self.roleDict = {}

    @commands.Cog.listener()
    async def on_ready(self):

        self.guild = self.bot.guild

        for r in self.guild.roles:
            if r.color == discord.Color.from_rgb(230, 126, 34):
                self.pronounDict.append(r)
            elif r.color == discord.Color.from_rgb(151, 156, 159):
                self.gamesDict.append(r)
            elif r.color == discord.Color.from_rgb(32, 102, 148):
                self.locationDict.append(r)
            else:
                self.roleDict[r.name] = r

        self.pronounDict.reverse()
        self.gamesDict.reverse()
        self.locationDict.reverse()
        print(ts.get_time_stamp(), "Created Role Manager")

        print(ts.get_time_stamp(), "Establishing Roles View")
        asyncio.get_event_loop().create_task(self.create_role_buttons(False))

    async def create_role_buttons(self, send_new):

        pronoun_view = discord.ui.View(timeout=None)
        for role in self.pronounDict:
            pronoun_view.add_item(RoleButton(role, style=discord.ButtonStyle.green))

        games_view = discord.ui.View(timeout=None)
        for role in self.gamesDict:
            games_view.add_item(RoleButton(role, style=discord.ButtonStyle.gray))

        location_view = discord.ui.View(timeout=None)
        for role in self.locationDict:
            location_view.add_item(RoleButton(role, style=discord.ButtonStyle.blurple))

        comrade_view = discord.ui.View(timeout=None)
        comrade_view.add_item(RoleButton(self.roleDict["Comrades"], style=discord.ButtonStyle.red))

        if send_new:
            await self.bot.channelDict["roles"].send("**Pronouns (You can select multiple)**", view=pronoun_view)
            await self.bot.channelDict["roles"].send("**Games**", view=games_view)
            await self.bot.channelDict["roles"].send("**Location**", view=location_view)
            await self.bot.channelDict["roles"].send("**Basedness**", view=comrade_view)
            print(ts.get_time_stamp(), "Created New Roles View")
        else:
            self.bot.add_view(pronoun_view)
            self.bot.add_view(games_view)
            self.bot.add_view(location_view)
            self.bot.add_view(comrade_view)
            print(ts.get_time_stamp(), "Reattached to Roles View")

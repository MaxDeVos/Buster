import discord


class DatabaseModel:
    def __init__(self, bot, message: discord.Message):
        self.bot = bot
        self.message = message
        self.rawLines = None
        self.table_name = None
        self.column_names = []
        self.data = {}
        self.reload()

    async def update_entry(self, col_id, column, entry):
        column = column # used to be casted to int()
        self.data[col_id][column] = entry
        await self.rewrite_table()

    async def rewrite_table(self):
        lines = [self.table_name, ','.join(self.column_names)]
        for row in self.data:
            row_out = ""
            for entry in self.data[row]:
                row_out += f"{entry},"
            row_out.removesuffix(",")
            lines.append(row_out)

        out = '\n'.join(lines)
        await self.message.edit(content=out)
        self.bot.dispatch("database-update", self.table_name, self.data)

    async def add_row(self, new_data, suspend_rewrite=False):
        self.data[new_data[0]] = new_data
        if not suspend_rewrite:
            await self.rewrite_table()

    async def remove_row(self, row_id, suspend_rewrite=False):
        del self.data[row_id]
        if not suspend_rewrite:
            await self.rewrite_table()

    def reload(self):
        self.rawLines = self.message.content.split("\n")
        if len(self.rawLines) < 2:
            raise Exception("Malformed table. Needs title and header row")
        self.table_name = self.rawLines[0]
        self.column_names = self.rawLines[1].split(",")
        self.data = {}

        for i in range(2, len(self.rawLines)):
            cols = self.rawLines[i].split(",")
            self.data[cols[0]] = cols

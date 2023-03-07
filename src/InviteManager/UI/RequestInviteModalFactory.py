from discord import InputTextStyle, Interaction, Message
from discord.ui import Modal, InputText

from src.DatabaseCog import DatabaseFactories
from src.DatabaseCog.DatabaseFactories import generate_invite_queue_db
from src.InviteManager.VoteModel import VoteModel


class RequestInviteModalFactory(Modal):

    def __init__(self, invite_cog, user, *children: InputText, title: str):
        super().__init__(*children, title=title)
        self.invite_cog = invite_cog
        self.bot = invite_cog.bot
        self.user = user
        self.children = []
        self.add_item(InputText(label="Real Name", placeholder="Joe Rogan"))
        self.add_item(InputText(label="Discord Username", placeholder="jamiePullThatUP#6969"))
        self.add_item(
            InputText(
                label="Write a bit about them",
                placeholder="Joe Rogan was present at my birth and he is the most racist person I know",
                style=InputTextStyle.long,
            )
        )

    async def callback(self, interaction: Interaction):
        await self.invite_cog.invite_modal_callback(interaction, modal_results=self.children)

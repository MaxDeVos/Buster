import discord


class AdmissionVoteButton(discord.ui.Button):

    def __init__(self, parent, label, invite_data, style=discord.enums.ButtonStyle.primary):
        """
        A button for one role. `custom_id` is needed for persistent views.
        :param InviteCog parent:
        :param str label:
        :param InviteQueueEntry invite_data
        """
        super().__init__(
            label=label,
            style=style,
            custom_id=f"{invite_data.entry_id}{label.lower()}",
        )
        self.parent = parent
        self.invite_data = invite_data

        if label.lower() == "yes":
            self.style = discord.enums.ButtonStyle.green
        elif label.lower() == "no":
            self.style = discord.enums.ButtonStyle.red
        elif label.lower() == "abstain":
            self.style = discord.enums.ButtonStyle.gray
        else:
            raise Exception("Button label isn't \"Yes\", \"No\", or \"Abstain\"")

        self.vote = label.lower()

    async def callback(self, interaction: discord.Interaction):
        await self.parent.handle_vote_event(interaction, self.invite_data.entry_id, self.vote)

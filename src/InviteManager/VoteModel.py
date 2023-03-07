from enum import Enum

from discord import Interaction, Message, utils, Member, Guild

from src.DatabaseCog.TableEntries import TableEntry


def generate_invite_queue_entry_from_database_string(row):
    entry_id = row[0]
    real_name = row[1]
    username = row[2]
    description = row[3]
    inviter_id = row[4]
    vote_message_id = row[5]
    veto_pending = row[6]

    out = VoteModel(entry_id=entry_id, inviter_id=inviter_id, vote_message_id=vote_message_id)
    out.real_name = real_name
    out.username = username
    out.description = description
    out.veto_pending = veto_pending

    return out


class VoteModel(TableEntry):
    interaction: Interaction
    original_response: Message

    def __init__(self, interaction=None, children=None, entry_id=None, inviter_id=None, vote_message_id=None,
                 veto_pending=False):

        if interaction:
            super().__init__(interaction.id, utils.snowflake_time(interaction.id))
            self.interaction = interaction
            self.inviter_id = self.interaction.user.id
        else:
            super().__init__(entry_id, utils.snowflake_time(int(vote_message_id)))
            self.inviter_id = inviter_id

        if children:
            self.user_responses = children
            self.real_name = self.user_responses[0].value
            self.username = self.user_responses[1].value
            self.description = self.user_responses[2].value
        else:
            self.real_name = ""
            self.username = ""
            self.description = ""

        self.votes_yes_id = f"{self.entry_id}yes"
        self.votes_no_id = f"{self.entry_id}no"
        self.votes_abstain_id = f"{self.entry_id}abstain"

        self.vote_message_id = vote_message_id

        self.votes_yes = []
        self.votes_no = []
        self.votes_abstain = []

        self.veto_pending = veto_pending

    def generate_votes_yes_table_entry(self):
        return [self.votes_yes_id, self.votes_yes]

    def generate_votes_no_table_entry(self):
        return [self.votes_no_id, self.votes_no]

    def generate_votes_abstain_table_entry(self):
        return [self.votes_abstain_id, self.votes_abstain]

    # returns if vote was successfully processed
    def add_yes_vote(self, user_id):
        if user_id in self.votes_yes:
            self.votes_yes.remove(user_id)
            return False
        if user_id in self.votes_abstain:
            self.votes_abstain.remove(user_id)
        if user_id in self.votes_no:
            self.votes_no.remove(user_id)
        self.votes_yes.append(user_id)
        return True

    # returns if vote was successfully processed
    def add_no_vote(self, user_id):
        if user_id in self.votes_no:
            self.votes_no.remove(user_id)
            return False
        if user_id in self.votes_abstain:
            self.votes_abstain.remove(user_id)
        if user_id in self.votes_yes:
            self.votes_yes.remove(user_id)
        self.votes_no.append(user_id)
        return True

    # returns if vote was successfully processed
    def add_abstain_vote(self, user_id):
        if user_id in self.votes_abstain:
            self.votes_abstain.remove(user_id)
            return False
        if user_id in self.votes_no:
            self.votes_no.remove(user_id)
        if user_id in self.votes_yes:
            self.votes_yes.remove(user_id)
        self.votes_abstain.append(user_id)
        return True

    def generate_table_entry(self):
        return [self.entry_id, self.real_name, self.username, self.description, self.inviter_id, self.vote_message_id,
                self.veto_pending]

    def generate_non_abstain_vote_percentages(self, total_members):
        non_abstained_members = total_members - len(self.votes_abstain)
        if non_abstained_members == 0:
            return None
        yes_percentage = 100 * len(self.votes_yes) / non_abstained_members
        no_percentage = 100 - yes_percentage
        return [yes_percentage, no_percentage]

    async def generate_vote_message(self, bot, result=None):
        user: Member = await bot.fetch_user(self.inviter_id)

        guild_members = await bot.determine_guild_users()

        lines = []

        lines.append("**FINAL VOTE RESULTS**\n")
        lines.append(
            f"Vote on whether or not to allow **{self.real_name}** to enter *de_bunker*\n")
        lines.append(f"The following message about {self.real_name} was provided by {user.mention}:")
        lines.append(f"```{self.description}```\n")

        if result is None:
            lines.append("To anonymously veto this admission, DM this code to Buster.\n")
            lines.append(
                "Afterwards, you may delete the message. All logs and records of your veto will be wiped instantly.\n")
            lines.append("In order to verify your anonymity, the veto will not be shown until the vote is over.")
            lines.append(f"```{self.entry_id}```\n")

        if self.generate_non_abstain_vote_percentages(guild_members) is None:
            return ''.join(lines)
        else:
            num_bar_chars = 30

            yes_percent = self.generate_non_abstain_vote_percentages(guild_members)[0]
            no_percent = self.generate_non_abstain_vote_percentages(guild_members)[1]
            vote_decimal = yes_percent / 100.0
            num_yes_chars = int(round(vote_decimal * num_bar_chars, 0))
            num_no_chars = num_bar_chars - num_yes_chars

            if result is None:
                lines.append(f"**Current vote tally**```")
            elif result == "passed":
                lines.append(f"**Final Result: *PASSED***```")
            elif result == "failed":
                lines.append(f"**Final Result: *FAILED***```")
            elif result == "vetoed":
                lines.append(f"**Final Result: *VETOED***```")

            lines.append(f"YES: [{'=' * num_yes_chars}{' ' * num_no_chars}] | {yes_percent}%\n")
            lines.append(f"NO:  [{'=' * num_no_chars}{' ' * num_yes_chars}] | {no_percent}%")
            if len(self.votes_abstain) > 0:
                lines.append(f"\nABSTAIN: {len(self.votes_abstain)} votes")

            if guild_members is not None:
                lines.append(f"\n\nVotes Registered: {self.get_total_votes()}/{guild_members}")

            lines.append("```")
            return ''.join(lines)

    def process_veto(self):
        self.veto_pending = True

    def get_total_votes(self):
        return len(self.votes_no) + len(self.votes_yes) + len(self.votes_abstain)

    async def has_vote_passed(self, bot):
        total_percents = self.generate_non_abstain_vote_percentages(await bot.determine_guild_users())
        if total_percents is None:
            return False
        return total_percents[0] > 75

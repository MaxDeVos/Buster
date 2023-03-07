import os

import discord
from discord import ApplicationContext, Interaction, Message, NotFound, Member, Invite
from discord.ext import commands

from src import Utils
from src.InviteManager.VoteModel import VoteModel, generate_invite_queue_entry_from_database_string
from src.InviteManager.UI.AdmissionVoteButton import AdmissionVoteButton
from src.InviteManager.UI.RequestInviteModalFactory import RequestInviteModalFactory
from src.TimestampGenerator import TimestampGenerator

ts = TimestampGenerator("INVT")


class InviteCog(commands.Cog):
    active_votes: dict[int, VoteModel]

    def __init__(self, bot):
        self.bot = bot
        self.active_votes = {}
        ts.info("Starting Invite Management System")

    @commands.Cog.listener()
    async def on_database_ready(self):
        """
        Waits for database to report a ready state (after bot's on_ready), and fires build_vote_models_from_database()
        """
        await self.build_vote_models_from_database()

    @commands.slash_command(guild_ids=[int(os.environ.get("GUILD_ID"))])
    async def invite(self, ctx: ApplicationContext):
        ts.info(f"Generating Invite Request for {ctx.user.name}")
        modal = RequestInviteModalFactory(self, ctx.user, title="Invite Request")
        await ctx.send_modal(modal)

    def generate_admission_vote_view(self, vote_model):
        """
        Generates View containing 3 vote buttons (yes, no, abstain) with their callbacks pointed at handle_vote_event()
        :param VoteModel vote_model:
        :returns: AdmissionVoteView admission_vote_view:
        """
        admission_vote_view = discord.ui.View(timeout=None)
        admission_vote_view.add_item(AdmissionVoteButton(self, "Yes", vote_model))
        admission_vote_view.add_item(AdmissionVoteButton(self, "No", vote_model))
        admission_vote_view.add_item(AdmissionVoteButton(self, "Abstain", vote_model))
        return admission_vote_view

    async def invite_modal_callback(self, interaction, modal_results):
        """
        Fired when the user has submitted the Invite User modal, called from the callbacks of the vote buttons.
        Creates and populates InviteQueueEntry object and adds it to the active_votes dictionary.
        Adds appropriate database rows into InviteQueue and AnonymousVoteTallies.
        Creates vote View and sends it in a message in #admissions-council
        :param Interaction interaction: from the modal
        :param [] modal_results: responses from the modal in order: [real name, username, description]
        """
        ts.info("Invite Modal Completed. Processing Callback")
        ts.info("Generating InviteQueue Entry")
        vote_model = VoteModel(interaction, modal_results)
        self.active_votes[vote_model.entry_id] = vote_model
        self.bot.dispatch("database_query_add_row", "InviteQueue", vote_model.generate_table_entry())

        ts.info("Replied to user. Generating new new voter database entries.")
        self.bot.dispatch("database_query_add_row", "AnonymousVoteTally", vote_model.generate_votes_yes_table_entry(), True)
        self.bot.dispatch("database_query_add_row", "AnonymousVoteTally", vote_model.generate_votes_no_table_entry(), True)
        self.bot.dispatch("database_query_add_row", "AnonymousVoteTally", vote_model.generate_votes_abstain_table_entry(), False)

        admission_vote_view = self.generate_admission_vote_view(vote_model)
        msg_content = await vote_model.generate_vote_message(self.bot)
        vote_msg: Message = await self.bot.channelDict["admissions-council"].send(content=msg_content,
                                                                                  view=admission_vote_view)
        self.active_votes[vote_model.entry_id].vote_message_id = vote_msg.id

        ts.info("Successfully created vote message. Writing vote message ID to database")
        self.bot.dispatch("database_query_change", "InviteQueue", vote_model.entry_id, 5, vote_msg.id)

        await interaction.response.send_message("Your invite request has been processed and the vote has been "
                                                "successfully created. Thank you.", ephemeral=True)

    async def handle_vote_event(self, interaction, vote_id, vote_yes):
        """
        Fired when a user clicks a vote option on the anonymous vote message. Called by the callback of the admission
        vote buttons @ at AdmissionVoteButton.callback()`.
        Checks if the vote is valid, and if it is, rewrite the AnonymousVoteTally
        Inform the user via ephemeral message that the vote has been accepted/rejected
        :param Interaction interaction: from the vote button
        :param int vote_id:
        :param boolean vote_yes:
        """
        vote_model = self.active_votes[vote_id]
        if vote_yes == "yes":
            vote_added = self.active_votes[vote_id].add_yes_vote(interaction.user.id)
        elif vote_yes == "no":
            vote_added = self.active_votes[vote_id].add_no_vote(interaction.user.id)
        else:
            vote_added = self.active_votes[vote_id].add_abstain_vote(interaction.user.id)

        self.bot.dispatch("database_query_replace_row", "AnonymousVoteTally", vote_model.votes_yes_id,
                          vote_model.generate_votes_yes_table_entry(), True)
        self.bot.dispatch("database_query_replace_row", "AnonymousVoteTally", vote_model.votes_no_id,
                          vote_model.generate_votes_no_table_entry(), True)
        self.bot.dispatch("database_query_replace_row", "AnonymousVoteTally", vote_model.votes_abstain_id,
                          vote_model.generate_votes_abstain_table_entry(), False)

        await self.regenerate_vote_message(vote_model)
        if vote_added:
            await interaction.response.send_message("This vote **(and only this vote)** have been processed. If you "
                                                    "change your mind, feel free to vote again.", ephemeral=True)
        else:
            await interaction.response.send_message("Your vote has been removed.", ephemeral=True)

        if vote_model.get_total_votes() == await self.determine_guild_users():
            await self.handle_vote_end(vote_id)

    async def regenerate_vote_message(self, vote_model):
        """
        Calculates new vote message content and edits the vote message accordingly
        :param VoteModel vote_model:
        """
        msg = await self.bot.channelDict["admissions-council"].fetch_message(vote_model.vote_message_id)
        msg_content = await vote_model.generate_vote_message(self.bot)
        await msg.edit(content=msg_content)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """
        Fires on a message being received. Checks if the message is a veto, and if it is, marks the vote as a having
        a pending veto in the model and updates the database to reflect this
        :param Message message: the DM containing the vote_id to veto
        """
        if message.guild is None and not message.author.bot:
            try:
                vote_id = int(message.content)
                self.active_votes[vote_id].process_veto()
                new_row = self.active_votes[vote_id].generate_table_entry()
                self.bot.dispatch("database_query_replace_row", "InviteQueue", vote_id, new_row, False)
                await message.reply("The veto has been processed. Feel free to dismiss this message and delete your DM."
                                    , ephemeral=True)
            except ValueError:
                ts.warn(f"Received DM that wasn't a valid veto from {message.author.name}: {message.content}")
            except Exception as e:
                ts.error("Failure processing veto!")
                await message.reply("Something is fucked, sorry. Talk to max", ephemeral=True)
                print(e)

    async def build_vote_models_from_database(self):
        """
        Loads all entries in the InviteQueue and AnonymousVoteTally database tables
        Builds one prototype vote model object from each row in InviteQueue
            Attempts to fetch vote message in #admissions-council exists
            Attempts to attach the 3 respective AnonymousVoteTally rows (yes, no, abstain)
            Attempts to construct 3-button view and reattach it to the bot
        If any of the previous steps fail, most likely the first one, the vote is cleared and marked as orphaned
        """
        ts.info("Reconstructing vote models from database")
        invite_queue = await self.bot.query_database("InviteQueue")
        anonymous_vote_tally = await self.bot.query_database("AnonymousVoteTally")

        if invite_queue is None:
            ts.info("No database voters found")
            return

        for row in invite_queue:
            vote_model = generate_invite_queue_entry_from_database_string(invite_queue[row])
            try:
                ts.info(f"Attempting to reconstructed voter {vote_model.entry_id}")
                await self.bot.channelDict["admissions-council"].fetch_message(vote_model.vote_message_id)
                ts.info(f"Found voter message for {vote_model.entry_id}")
                vote_model.votes_no = Utils.array_string_to_list(anonymous_vote_tally[vote_model.votes_no_id][1], int)
                vote_model.votes_yes = Utils.array_string_to_list(anonymous_vote_tally[vote_model.votes_yes_id][1], int)
                vote_model.votes_abstain = Utils.array_string_to_list(anonymous_vote_tally[vote_model.votes_abstain_id][1], int)
                ts.info("Reattached y/n/a voter database entries")
                admission_vote_view = self.generate_admission_vote_view(vote_model)
                self.bot.add_view(admission_vote_view)
                ts.info("Reconstructed View and reattached to bot")
                ts.info(f"Successfully reconstructed valid voter {vote_model.entry_id}")

                self.active_votes[vote_model.entry_id] = vote_model
            except NotFound as e:
                ts.warn(f"Found orphaned admission vote {vote_model.entry_id}. Removing from database")
                self.delete_vote_from_database(vote_model)

    async def handle_vote_end(self, vote_id):
        """
        Fired from handle_vote_event when number of votes = number of non-bot members in guild.
        If the vote passes, it generates the invite and DMs it to the inviter.
        In all cases, the original vote message is updated to reflect the final result of the vote.
        Removes the voter's records from the database, leaving only the message in #admissions-council
        :param int vote_id: entry_id of vote that ended
        """
        vote_model = self.active_votes[vote_id]

        if vote_model.veto_pending:
            await self.mark_vote_finished(vote_model, "vetoed")
        else:
            if await vote_model.has_vote_passed(self.bot):
                await self.send_invite_to_inviter(vote_model)
                await self.mark_vote_finished(vote_model, "passed")
            else:
                await self.mark_vote_finished(vote_model, "failed")
        self.delete_vote_from_database(vote_model)

    async def send_invite_to_inviter(self, vote_model):
        """
        Generates and sends single-use invite to the inviter
        :param VoteModel vote_model: Vote model to generate invite from
        """
        inviter = await self.bot.guild.fetch_member(vote_model.inviter_id)
        invite: Invite = await self.bot.channelDict["server-announcements"].create_invite(max_uses=1, unique=True)
        await inviter.send(f"The admission vote for {vote_model.real_name} [{vote_model.username}] has passed. "
                           f"Here is their invite.```{invite.url}```")
        await inviter.send(f"{invite.url}")

    async def mark_vote_finished(self, vote_model, result):
        """
        Updates the content of a voter message to reflect finality and removes its View containing the 3 vote buttons
        :param VoteModel vote_model: Vote model to update
        :param str result: "passed", "failed", or "vetoed"
        """
        vote_message: Message = await self.bot.channelDict["admissions-council"]. \
            fetch_message(vote_model.vote_message_id)
        updated_message_content = await vote_model.generate_vote_message(self.bot, result=result)
        await vote_message.edit(content=updated_message_content, view=None)

    def delete_vote_from_database(self, vote_model):
        """
        Clears all rows related to vote model from tables InviteQueue and AnonymousVoteTally
        Row removed from InviteQueue (entry_id=12345678):  12345678
        Rows removed from InviteQueue (entry_id=12345678): 12345678yes, 12345678no, 12345678abstain
        Also deletes VoteModel from self.active_votes
        :param VoteModel vote_model: Vote Model to remove from database
        """
        ts.info(f"Deleting vote {vote_model.entry_id} from database")
        self.bot.dispatch("database_query_remove", "InviteQueue", vote_model.entry_id)
        self.bot.dispatch("database_query_remove", "AnonymousVoteTally", f"{vote_model.entry_id}yes")
        self.bot.dispatch("database_query_remove", "AnonymousVoteTally", f"{vote_model.entry_id}no")
        self.bot.dispatch("database_query_remove", "AnonymousVoteTally", f"{vote_model.entry_id}abstain")
        if vote_model.entry_id in self.active_votes:
            del self.active_votes[vote_model.entry_id]
        ts.info(f"Successfully cleared vote {vote_model.entry_id} and its 3 vote entries from the database")

    @commands.Cog.listener()
    async def on_manual_database_update(self, table_name, table, message):
        """
        Replaces all VoteModels with freshly reloaded ones from the database.
        Determines if updates mean vote is finished, and rerenders the vote message accordingly.
        """
        ts.info("Manual database change detected. Rebuilding and refreshing vote models from database")
        await self.build_vote_models_from_database()
        for vote_model_id in self.active_votes:
            vote_model = self.active_votes[vote_model_id]
            if await vote_model.has_vote_passed(self.bot) \
                    or vote_model.get_total_votes() == await self.bot.determine_guild_users():
                await self.handle_vote_end(vote_model_id)
            await self.regenerate_vote_message(vote_model)
            self.active_votes[vote_model_id] = vote_model

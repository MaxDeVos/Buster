import discord


class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, style=discord.enums.ButtonStyle.primary):
        """
        A button for one role. `custom_id` is needed for persistent views.
        """
        super().__init__(
            label=role.name,
            style=style,
            custom_id=str(role.id),
        )

    async def callback(self, interaction: discord.Interaction):
        """This function will be called any time a user clicks on this button.
        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object that was created when a user clicks on a button.
        """
        # Figure out who clicked the button.
        user = interaction.user
        # Get the role this button is for (stored in the custom ID).
        role = interaction.guild.get_role(int(self.custom_id))

        if role is None:
            # If the specified role does not exist, return nothing.
            # Error handling could be done here.
            return

        # Add the role and send a response to the uesr ephemerally (hidden to other users).
        if role not in user.roles:
            # Give the user the role if they don't already have it.
            await user.add_roles(role)
            await interaction.response.send_message(f"You have been given the role {role.mention}", ephemeral=True)
        else:
            # Else, Take the role from the user
            await user.remove_roles(role)
            await interaction.response.send_message(
                f"The {role.mention} role has been taken from you", ephemeral=True
            )
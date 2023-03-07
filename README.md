<img src="BusterLogo.png">
<p align="center"><em>Single-Guild minimal, secure, fully portable Discord bot for managing protected, tight-knit communities.</em></p>

***
As the threat against marginalized communities continues to grow, the need for protected social spaces becomes stronger. Buster is the solution that I created for the people in my life, and perhaps it could be of use to you as well.


<h1>Features</h1>

<h3>Anonymous invite approval system</h3>
<p>In order to protect the people within your community, Buster employs a unique join system which requires the anonymous approval (or abstention) of all members of the server, and provides the opportunity for anybody to anonomously veto any admission via a message sent externally (a DM to Buster).</p>
<div style="display:flex;">
  <img align="top" src="screenshots/invite_request_modal.png" height="415px"; alt="Example of post that will be pinned">
  <img align="top" src="screenshots/invite_request_menu.png" height="415px"; alt="Example of pinned post">
</div>

<h3>Internal Database</h3>
<p>Contains "database-to-channel" (a term you'll only hear once) middleware which allows for use of one TextChannel as an event-driven database, with each message representing a table. This has the benefit of allowing the bot's code to be entirely portable, all data ABOUT the server is stored IN the server. No CVS files or MySQL database to carry around. Server goes down? Fire it up on your laptop.</p>

<h3>Independent Pin System</h3>
<p>50 pinned posts isn't nearly enough for most situations. Buster provides a means of democratically saving posts onto a pin board. When some number of users (of your selection) use the 📌 emoji on a post, it will be copied into the #pins channel with a link to the original post</p>
<div style="display:flex">
  <img src="screenshots/to_pin.png" height="200px" alt="Example of post that will be pinned">
  <img src="screenshots/pinned.png" height="200px" alt="Example of pinned post">
</div>

<h3>Translation Engine</h3>
<p>Buster uses the Google Translate API to provide free translation to users with specified lanuage roles.</p>
<img src="screenshots/translation.png" height="200px" alt="Translation example">

<h3>Emoji Registration System</h3>
<p>Depending on the size of your guild and your preferences, Buster can either report any emoji changes made by users, or provide an interface for users to offer new emojis to be voted on by the rest of the server.</p>
<img src="screenshots/emoji_update.png" height="200px" alt="Example of notification about emoji change">

from GompeiFunctions import make_ordinal, time_delta_string, load_json, save_json, parse_id
from Permissions import moderator_perms, administrator_perms
from discord.ext import commands
from datetime import timedelta
from datetime import datetime

import pytimeparse
import dateparser
import asyncio
import discord
import os


class Administration(commands.Cog):
    """
    Administration tools
    """

    def __init__(self, bot):
        self.warns = load_json(os.path.join("config", "warns.json"))
        self.bot = bot

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def echo(self, ctx, channel):
        """
        Forwards message / attachments appended to the command to the given channel
        :param ctx: context object
        :param channel: channel to send the message to
        """
        # Check if the channel exists
        echo_channel = ctx.guild.get_channel(int(channel[2:-1]))
        if echo_channel is not None:

            # Check for attachments to forward
            attachments = []
            if len(ctx.message.attachments) > 0:
                for i in ctx.message.attachments:
                    attachments.append(await i.to_file())

            # Get message content and check length
            message = ctx.message.content[7 + len(channel):]
            if len(message) > 0:
                message = await echo_channel.send(message, files=attachments)
                await ctx.send("Message sent (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(message.channel.id) + "/" + str(message.id) + ">)")
            elif len(attachments) > 0:
                message = await echo_channel.send(files=attachments)
                await ctx.send("Message sent (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(message.channel.id) + "/" + str(message.id) + ">)")
            else:
                await ctx.send("No content to send.")
        else:
            await ctx.send("Not a valid channel")

    @echo.error
    async def echo_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print("!ERROR! " + str(ctx.author.id) + " did not have permissions for echo command")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Command is missing arguments")
        else:
            print(error)

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["echoEdit"])
    @commands.check(moderator_perms)
    async def echo_edit(self, ctx, message_link):
        # Get message and channel ID from the message_link
        message_id = int(message_link[message_link.rfind("/") + 1:])
        shortLink = message_link[:message_link.rfind("/")]
        channel_id = int(shortLink[shortLink.rfind("/") + 1:])

        # Check if the channel exists
        channel = ctx.guild.get_channel(channel_id)
        if channel is None:
            await ctx.send("Not a valid link to message")
        else:
            # Check if the message exists
            message = await channel.fetch_message(message_id)
            if message is None:
                await ctx.send("Not a valid link to message")
            else:
                # Check if Gompei is author of the message
                if message.author.id != self.bot.user.id:
                    await ctx.send("Cannot edit a message that is not my own")
                else:
                    # Read new message content and edit message
                    newMessage = ctx.message.content[10 + len(message_link):]

                    await message.edit(content=newMessage)
                    await ctx.send("Message edited (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(channel_id) + "/" + str(message_id) + ">)")

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["pmEcho", "echoPM"])
    @commands.check(moderator_perms)
    async def echo_pm(self, ctx, user):
        """
        Forwards given message / attachments to give user
        """
        # Get member
        member = ctx.guild.get_member(parse_id(user))

        if member is None:
            await ctx.send("Not a valid member")
            return

        # Read attachments and message
        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        message = ctx.message.content[9 + len(user):]

        # Send message to user via DM
        if len(message) > 0:
            message = await member.send(message, files=attachments)
            await ctx.send("Message sent (<https://discordapp.com/channels/@me/" + str(message.channel.id) + "/" + str(message.id) + ">)")
        elif len(attachments) > 0:
            message = await member.send(files=attachments)
            await ctx.send("Message sent (<https://discordapp.com/channels/@me/" + str(message.channel.id) + "/" + str(message.id) + ">)")
        else:
            await ctx.send("No content to send")

        await ctx.message.add_reaction("👍")

    @echo_pm.error
    async def echo_pm_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print("!ERROR! " + str(ctx.author.id) + " did not have permissions for echo command")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Command is missing arguments")
        else:
            print(error)

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["pmEdit"])
    @commands.check(moderator_perms)
    async def pm_edit(self, ctx, user, message_link):
        # Get message ID from message_link
        message_id = int(message_link[message_link.rfind("/") + 1:])

        member = ctx.guild.get_member(parse_id(user))
        if member is None:
            await ctx.send("Not a valid user")
        else:
            channel = member.dm_channel
            if channel is None:
                channel = await member.create_dm()

            message = await channel.fetch_message(message_id)
            if message is None:
                await ctx.send("Not a valid link to message")
            else:
                if message.author.id != self.bot.user.id:
                    await ctx.send("Cannot edit a message that is not my own")
                else:
                    new_message = ctx.message.content[10 + len(message_link) + len(user):]

                    await message.edit(content=new_message)
                    await ctx.send("Message edited (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(channel.id) + "/" + str(message_id) + ">)")

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["react", "echoReact"])
    @commands.check(moderator_perms)
    async def echo_react(self, ctx, message_link, emote):
        message_id = int(message_link[message_link.rfind("/") + 1:])
        short_link = message_link[:message_link.rfind("/")]
        channel_id = int(short_link[short_link.rfind("/") + 1:])

        channel = ctx.guild.get_channel(channel_id)
        if channel is None:
            await ctx.send("Not a valid link to message")
        else:
            message = await channel.fetch_message(message_id)
            if message is None:
                await ctx.send("Not a valid link to message")
            else:
                await message.add_reaction(emote)
                await ctx.message.add_reaction("👍")

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["reactRemove", "echoRemoveReact"])
    @commands.check(moderator_perms)
    async def echo_remove_react(self, ctx, message_link, emote):
        message_id = int(message_link[message_link.rfind("/") + 1:])
        short_link = message_link[:message_link.rfind("/")]
        channel_id = int(short_link[short_link.rfind("/") + 1:])

        channel = ctx.guild.get_channel(channel_id)
        if channel is None:
            await ctx.send("Not a valid link to message")
        else:
            message = await channel.fetch_message(message_id)
            if message is None:
                await ctx.send("Not a valid link to message")
            else:
                await message.remove_reaction(emote)
                await ctx.message.add_reaction("👍")

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def purge(self, ctx, number):
        """
        Purges a number of messages in channel used
        :param ctx: context object
        :param number: number of messages to purge
        """
        await ctx.channel.purge(limit=int(number) + 1)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print("!ERROR! " + str(ctx.author.id) + " did not have permissions for purge command")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Command is missing arguments")
        else:
            print(error)

    @commands.guild_only()
    @commands.command(pass_context=True, name="spurge")
    @commands.check(moderator_perms)
    async def selective_purge(self, ctx, user, number):
        """
        Purges messages from a specific user in the channel
        :param ctx: context object
        :param user: user to purge
        :param number: number of messages to purge
        """
        member = ctx.guild.get_member(parse_id(user))

        messages = [ctx.message]
        old_message = ctx.message
        count = 0

        while count < int(number):
            async for message in ctx.message.channel.history(limit=int(number), before=old_message, oldest_first=False):
                if message.author == member:
                    count += 1
                    messages.append(message)

                    if count == int(number):
                        break

                old_message = message.created_at

        await ctx.channel.delete_messages(messages)

    @selective_purge.error
    async def selective_purge_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print("!ERROR! " + str(ctx.author.id) + " did not have permissions for selective purge command")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Command is missing arguments")
        else:
            print(error)

    @commands.command(pass_context=True, aliases=["tPurge", "timePurge"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def time_purge(self, ctx, channel, time1, time2=None):
        channel = ctx.guild.get_channel(parse_id(channel))

        # If channel does not exist
        if channel is None:
            await ctx.send("Not a valid channel")
            return

        after_date = dateparser.parse(time1)

        if after_date is None:
            await ctx.send("Not a valid after time/date")
            return

        if time2 is None:
            offset = datetime.utcnow() - datetime.now()
            messages = await channel.history(limit=None, after=after_date + offset).flatten()
        else:
            before_date = dateparser.parse(time2)

            if before_date is None:
                await ctx.send("Not a valid before time/date")
                return

            offset = datetime.utcnow() - datetime.now()
            messages = await channel.history(limit=None, after=after_date + offset, before=before_date + offset).flatten()

        if len(messages) == 0:
            await ctx.send("There are no messages to purge in this time frame")
            return

        response = "You are about to purge " + str(len(messages)) + " message(s) from " + channel.name
        if time2 is None:
            response += " after " + str(after_date) + ".\n"
        else:
            response += " between " + str(after_date) + " and " + str(before_date) + ".\n"

        response += "The purge will start at <" + messages[0].jump_url + "> and end at <" + messages[-1].jump_url + ">.\n\nAre you sure you want to proceed? (Y/N)"

        def check_author(message):
            return message.author.id == ctx.author.id

        await ctx.send(response)

        response = await self.bot.wait_for('message', check=check_author)
        if response.content.lower() == "y" or response.content.lower() == "yes":
            await channel.delete_messages(messages)
            await ctx.send("Successfully purged messages")
        else:
            await ctx.send("Cancelled purging messages")

    @commands.command(pass_context=True, aliases=["mPurge", "messagePurge"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def message_purge(self, ctx, channel, start_message, end_message=None):
        # Get channel
        channel = ctx.guild.get_channel(parse_id(channel))

        # If channel does not exist
        if channel is None:
            await ctx.send("Not a valid channel")
            return

        try:
            s_message = await channel.fetch_message(int(start_message[-18:]))
        except ValueError:
            await ctx.send("Not a valid message ID (start message)")
            return
        except discord.NotFound:
            await ctx.send("Could not find message in given channel")
            return

        if end_message is None:
            messages = await channel.history(limit=None, after=s_message.created_at).flatten()
            messages.insert(0, s_message)
        else:
            try:
                e_message = await channel.fetch_message(int(end_message[-18:]))
            except ValueError:
                await ctx.send("Not a valid message ID (start message)")
                return
            except discord.NotFound:
                await ctx.send("Could not find message in given channel")
                return

            messages = await channel.history(limit=None, after=s_message.created_at, before=e_message.created_at).flatten()
            messages.append(e_message)

        messages.insert(0, s_message)

        if len(messages) == 0:
            await ctx.send("You've selected no messages to purge")
            return

        response = "You are about to purge " + str(len(messages)) + " message(s) from " + channel.name

        response += "\nThe purge will start at <" + messages[0].jump_url + "> and end at <" + messages[-1].jump_url + ">.\n\nAre you sure you want to proceed? (Y/N)"

        def check_author(message):
            return message.author.id == ctx.author.id

        await ctx.send(response)

        response = await self.bot.wait_for('message', check=check_author)
        if response.content.lower() == "y" or response.content.lower() == "yes":
            await channel.delete_messages(messages)
            await ctx.send("Successfully purged messages")
        else:
            await ctx.send("Cancelled purging messages")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def mute(self, ctx, arg1, arg2):
        member = ctx.guild.get_member(parse_id(arg1))
        muted_role = ctx.guild.get_role(615956736616038432)

        # Is user already muted
        if muted_role in member.roles:
            await ctx.send("This member is already muted")
            return

        # Check role hierarchy
        if ctx.author.top_role.position <= member.top_role.position:
            await ctx.send("You're not high enough in the role hierarchy to do that.")
            return

        username = member.name + "#" + str(member.discriminator)

        seconds = pytimeparse.parse(arg2)
        if seconds is None:
            await ctx.send("Not a valid time, try again")

        delta = timedelta(seconds=seconds)
        reason = ctx.message.content[8 + len(arg1 + arg2):]
        if len(reason) < 1:
            await ctx.send("You must include a reason for the mute")
            return

        mute_time = time_delta_string(datetime.utcnow(), datetime.utcnow() + delta)

        await member.add_roles(muted_role)
        await ctx.send("**Muted** user **" + username + "** for **" + mute_time + "** for: **" + reason + "**")
        await member.send("**You were muted in the WPI Discord Server for " + mute_time + ". Reason:**\n> " + reason + "\n\nYou can repond here to contact WPI Discord staff.")

        await asyncio.sleep(seconds)

        await member.remove_roles(muted_role)
        await ctx.send("**Unmuted** user **" + username + "**")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Command is missing arguments: .mute <user> <minutes> <reason>")
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Invalid mute time")

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def warn(self, ctx, user):
        """
        Warns a specific user for given reason
        """
        member_id = parse_id(user)
        member = ctx.guild.get_member(member_id)

        if member is None:
            await ctx.send("Not a valid member")
            return

        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        message = ctx.message.content[7 + len(user):]
        if len(message) > 0:
            await member.send("You were warned in the WPI Discord Server. Reason:\n> " + message, files=attachments)
        else:
            await ctx.send("No warning to send")
            return

        if str(member_id) in self.warns:
            self.warns[str(member_id)].append(message)
        else:
            self.warns[str(member_id)] = [message]

        save_json(os.path.join("config", "warns.json"), self.warns)

        await ctx.send("Warning sent to " + member.display_name + " (" + str(member_id) + "), this is their " + make_ordinal(len(self.warns[str(member_id)])) + " warning")

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print("!ERROR! " + str(ctx.author.id) + " did not have permissions for warn command")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Command is missing arguments\n> warn [user/user_ID] [reason]")
        else:
            print(error)

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def warns(self, ctx, user=None):
        message = ""
        if user is None:
            if len(self.warns) == 0:
                message = "There are no warnings on this server"
            for member in self.warns:
                message += "Warnings for <@" + member + ">\n"
                count = 1
                for warn in self.warns[member]:
                    message += "__**" + str(count) + ".**__\n" + warn + "\n\n"
                    count += 1

                message += "\n\n"
        else:
            member_id = parse_id(user)
            if str(member_id) in self.warns:
                message = "Warnings for <@" + str(member_id) + ">\n"
                for warn in self.warns[str(member_id)]:
                    message += "> " + warn + "\n"
            else:
                message = "This user does not exist or has no warnings"

        if len(message) > 2000:
            n = 2000
            for index in range(0, len(message), n):
                await ctx.send(message[index: index + n])
        else:
            await ctx.send(message)

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["warnNote"])
    @commands.check(moderator_perms)
    async def warn_note(self, ctx, user):
        member_id = parse_id(user)
        member = ctx.guild.get_member(member_id)

        if member is None:
            await ctx.send("Not a valid member")
            return

        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        message = ctx.message.content[11 + len(user):]

        if str(member_id) in self.warns:
            self.warns[str(member_id)].append(message)
        else:
            self.warns[str(member_id)] = [message]

        save_json(os.path.join("config", "warns.json"), self.warns)

        await ctx.send("Warning added for " + member.display_name + " (" + str(member_id) + "), this is their " + make_ordinal(len(self.warns[str(member_id)])) + " warning")

    @commands.command(pass_context=True, aliases=["clearWarn"])
    @commands.check(moderator_perms)
    async def clear_warn(self, ctx, user):
        member_id = parse_id(user)
        if str(member_id) in self.warns:
            del self.warns[str(member_id)]
            await ctx.send("Cleared warnings for <@" + str(member_id) + ">")
            save_json(os.path.join("config", "warns.json"), self.warns)
        else:
            await ctx.send("This user does not exist or has no warnings")

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def lockdown(self, ctx):
        if len(ctx.message.content) > 10:
            lock_channel = ctx.guild.get_channel(parse_id(ctx.message.content[10:]))
            if lock_channel is None:
                await ctx.send("Not a valid channel to lockdown")
                return
        else:
            lock_channel = ctx.channel

        overwrite = lock_channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            await ctx.send("Channel is already locked down!")
        else:
            overwrite.update(send_messages=False)
            await lock_channel.send(":white_check_mark: **Locked down " + lock_channel.name + "**")
            await lock_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def unlock(self, ctx):
        if len(ctx.message.content) > 8:
            lock_channel = ctx.guild.get_channel(parse_id(ctx.message.content[8:]))
            if lock_channel is None:
                await ctx.send("Not a valid channel to unlock")
                return
        else:
            lock_channel = ctx.channel

        overwrite = lock_channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            overwrite.update(send_messages=None)
            await lock_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await lock_channel.send(":white_check_mark: **Unlocked " + lock_channel.name + "**")
        else:
            await ctx.send("Channel is not locked")

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    async def slowmode(self, ctx, channel, time):
        channel = ctx.guild.get_channel(parse_id(channel))
        if channel is None:
            await ctx.send("Not a valid channel")
        else:
            seconds = pytimeparse.parse(time)
            if seconds is None:
                await ctx.send("Not a valid time format, try again")
            elif seconds > 21600:
                await ctx.send("Slowmode delay is too long")
            else:
                await channel.edit(slowmode_delay=seconds)
                await ctx.send("Successfully set slowmode delay to " + str(seconds) + " seconds in #" + channel.name)

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(administrator_perms)
    async def kick(self, ctx, user):
        """
        Kicks a user from the server, requires a reason as well
        :param ctx: Context object
        :param user: User to kick
        """
        member = ctx.guild.get_member(parse_id(user))

        if member is None:
            await ctx.send("Could not find the member to kick")
        else:
            reason = ctx.message.content[ctx.message.content.find(" ") + len(user) + 2:]
            if len(reason) < 1:
                await ctx.send("Must include a reason with the kick")
            else:
                await member.send(member.guild.name + " kicked you for reason:\n> " + reason)
                await member.kick(reason=reason)
                await ctx.send("Successfully kicked user " + member.name + member.discriminator)

    @commands.guild_only()
    @commands.command(pass_context=True)
    @commands.check(administrator_perms)
    async def ban(self, ctx, user):
        """
        Bans a user from the server, requires a reason as well
        :param ctx: Context object
        :param user: User to ban
        """
        member = ctx.guild.get_member(parse_id(user))

        if member is None:
            await ctx.send("Could not find the member to kick")
        else:
            reason = ctx.message.content[ctx.message.content.find(" ") + len(user) + 2:]
            if len(reason) < 1:
                await ctx.send("Must include a reason with the ban")
            else:
                await member.send(member.guild.name + " banned you for reason:\n> " + reason)
                await member.kick(reason=reason)
                await ctx.send("Successfully banned user " + member.name + member.discriminator)

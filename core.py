ClippySettings = None
Forbidden = None

async def cmd_usage(client, message, cmds):
    try:
        if message.content.lower().startswith(ClippySettings.commandprefix + 'usage help'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "help`:\nDescription: Shows the help menu.\nUsage: `" + ClippySettings.commandprefix + "help`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage info'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "info`:\nDescription: Shows details about the bot.\nUsage: `" + ClippySettings.commandprefix + "info`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage calc'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "calc`:\nDescription: Solves basic math equations.\nUsage: `" + ClippySettings.commandprefix + "calc <equation>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage afk'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "afk`:\nDescription: Tells the channel that you are now afk.\nUsage: `" + ClippySettings.commandprefix + "afk`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage unafk'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "unafk`:\nDescription: Tells the channel that you are no longer afk.\nUsage: `" + ClippySettings.commandprefix + "unafk`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage ping'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "ping`:\nDescription: Tests to see if the bot is still alive.\nUsage: `" + ClippySettings.commandprefix + "ping`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage date'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "date`:\nDescription: **Will** show your current time/date. Currently it only shows the bots.\nUsage: `" + ClippySettings.commandprefix + "date <timezone>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage shoot'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "shoot`:\nDescription: Shoots a person.\nUsage: `" + ClippySettings.commandprefix + "shoot <@User>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage 8ball'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "8ball`:\nDescription: Tells your fortune.\nUsage: `" + ClippySettings.commandprefix + "8ball <message>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage rr'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "rr`:\nDescription: Simulates a game of Russian Roulette.\nUsage: `" + ClippySettings.commandprefix + "rr`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage say'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "say`:\nDescription: Makes the bot say a message.\nUsage: `" + ClippySettings.commandprefix + "say <message>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage avatar'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "avatar`:\nDescription: Gives the avatar of the mentioned user.\nUsage: `" + ClippySettings.commandprefix + "avatar <@User>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage timer'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "timer`:\nDescription: **Will** set a timer to remind you of something.\nUsage: `" + ClippySettings.commandprefix + "timer <seconds> <message>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage weather'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "weather`:\nDescription: **Will** show your current weather.\nUsage: `" + ClippySettings.commandprefix + "weather <location>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage join'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "join`:\nDescription: Makes the bot join the desired Discord link.\nUsage: `" + ClippySettings.commandprefix + "join <link>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage awwshit'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "awwshit`:\nDescription: Gives you a handy dandy meme.\nUsage: `" + ClippySettings.commandprefix + "awwshit`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage translate'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "translate`:\nDescription: **Will** translate a phrase.\nUsage: `" + ClippySettings.commandprefix + "translate '<message>' '<to-language>'`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage speak'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "speak`:\nDescription: Makes the bot say a text-to-speech message.\nUsage: `" + ClippySettings.commandprefix + "speak <message>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage roti'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "roti`:\nDescription: Gives you one of the 102 rules of the internet.\nUsage: `" + ClippySettings.commandprefix + "roti <1-102>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage usage'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "usage`:\nDescription: Gives a description of a command and how to use it.\nUsage: `" + ClippySettings.commandprefix + "usage <command>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage wiki'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "wiki`:\nDescription: Gives you info on the specified topic as well as a link for more info.\nUsage: `" + ClippySettings.commandprefix + "wiki <topic>`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage quote'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "quote`:\nDescription: A randomized quote to spruce up your day.\nUsage: `" + ClippySettings.commandprefix + "quote`.")
        elif message.content.lower().startswith(ClippySettings.commandprefix + 'usage emojis'):
            await client.send_message(message.channel, "Info for the command `" + ClippySettings.commandprefix + "emojis`:\nDescription: Type `" + ClippySettings.commandprefix + "emojis` for 4 helpful emojis, and `" + ClippySettings.commandprefix + "emojis long` for the link to the whole list.\nUsage: `" + ClippySettings.commandprefix + "emojis/emojis long`.")
    except Forbidden:
        pass

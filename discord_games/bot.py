import config
import discord

# need to allow matching intents on the bot admin page
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    # so bot doesn't respond to itself
    if message.author == client.user:
        return

    if message.content.lower().startswith('!simon'):
        #user_id = message.author.id
        embed = discord.Embed(title="🎮 Simon Says...",
                              description="Click the link below to start:",
                              color=0x00ff00)
        embed.add_field(name="Game Link",
                        #value="[Play Now](https://127.0.0.1:500/login?token={user_token})",
                        value="[Play Now](http://127.0.0.1:5000)",
                        inline=False)
        await message.reply(embed=embed)

#how do I know if the session has ended with a user?
#log everyone's user_id if they press play
#ping everyone after 24hrs from the first "play" announcing winners and asking to play now

client.run(config.BOT_TOKEN)

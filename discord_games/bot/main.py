import discord
import secrets
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # so bot doesn't respond to itself
    if message.author == client.user:
        return

    if message.content.lower().startswith('!simon'):
        user_id = message.author.id
        user_token = secrets.token_urlsafe(16)
        #store_token(user_id, user_token) and do a get_user_data(user_id) on on_play()

        embed = discord.Embed(title="🎮 Simon Says...",
                              description="Click the link below to start:",
                              color=0x00ff00)
        embed.add_field(name="Game Link",
                        #value="[Play Now](https://simonsays.com/play?token={user_token})",
                        value="[Play Now](http://127.0.0.1:5000)",
                        inline=False)
        await message.reply(embed=embed)

#how do I know if the session has ended with a user? webhook?
#log everyone's user_id if they press play
#ping everyone after 24hrs from the first "play" announcing winners and asking to play now

# portable way to get relative path
dname = os.path.dirname(__file__)
fname = os.path.join(dname, 'token.txt')
with open(fname, 'r') as file:
    token = file.readline().strip()
client.run(token)

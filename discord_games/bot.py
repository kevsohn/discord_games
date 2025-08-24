import requests
import discord
import config

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
        embed = discord.Embed(title="🎮 Simon Says...",
                              description="Click the link below to start:",
                              color=0x00ff00)
        embed.add_field(name="Game Link",
                        value=f"[Play Now]({config.BASE_URL}/login)",
                        inline=False)
        await message.reply(embed=embed)

# ping everyone after 24hrs from the first "play" announcing winners and asking to play now
# the first time the bot gets called into the server, set the announcement time 24h from this time
# then, run a background job to check every hour if 24h passed, and announce leaders for the day
# and reset time
'''
async def show_rankings():
    get_rankings()
    await message.send?()

async def get_rankings():
    r = requests.get(f"{config.BASE_URL}/api/rankings")
'''

client.run(config.BOT_TOKEN)

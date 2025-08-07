import discord

intents = discord.Intents.default()
# This example requires the 'message_content' intent.
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # so bot doesn't respond to itself
    if message.author == client.user:
        return

    #if message.content.lower().startswith("!minesweeper"):

    if message.content.lower().startswith('!simon'):
        embed = discord.Embed(title="🎮 Simon Says...",
                              description="Click the link below to start:",
                              color=0x00ff00)
        embed.add_field(name="Game Link", value="[Play Now](https://yourgame.com/play)", inline=False)
        #await message.channel.send(embed=embed)
        await message.reply(embed=embed)

with open('token.txt', 'r') as file:
    token = file.readline().strip()
client.run(token)

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

    if message.content.lower().startswith('!simon'):
        await message.reply('Hello! Do you want to play a game? :>', mention_author=True)

with open('token.txt', 'r') as file:
    token = file.readline().strip()
client.run(token)

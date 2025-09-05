import asyncio
import os

import discord
from discord.ext import commands

import config


class Simon(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # need to allow matching intents on the bot admin page
        intents.message_content = True
        intents.members = True
        description = 'Minigame Gauntlet Bot'
        super().__init__(command_prefix=config.CMD_PREFIX, intents=intents, description=description)

    async def setup_hook(self):
        # load cogs automatically
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'cogs')):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

    async def on_ready(self):
        print(f"🤖 Logged in as {self.user}")


async def main():
    bot = Simon()
    await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())


# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 23:53 2025

@author: kevsohn
"""

import os
import asyncio
import discord
from discord.ext import commands
import config

TOKEN = config.BOT_TOKEN
#GUILD = config.DISC_SERVER

print("INFO:----")
print(f'Server: {GUILD}')
print("--------")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = '''Minigame Gauntlet Discord Bot'''
bot = commands.Bot(command_prefix=['!simon'], description=description, intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

async def main():
    async with bot:
        await bot.load_extension("cogs.minigames_cog")
        await bot.start(TOKEN)

asyncio.run(main())

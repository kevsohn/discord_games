import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands

import config


class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.API_URL = config.BASE_URL+'/api'
        # start background reminder loop
        self.bot.loop.create_task(self.announce_rankings())


    @commands.command(name="play")
    async def link_games(self, ctx):
        """
        Command format: !play
        """
        embed = discord.Embed(
                title="🎮 Simon Says...",
                description="Click the link below to start:",
                color=0x00ff00
        )
        embed.add_field(
                name="Game Link",
                value=f"[Play Now]({config.BASE_URL}/login)",
                inline=False
        )
        await ctx.reply(embed=embed)


    @commands.command(name="rankings")
    async def get_rankings(self, ctx):
        """
        Command format: !rankings
        """
        #await ctx.message.delete()  # Delete the command message
        #await response_message.delete()  # Delete the bot's response


    async def announce_rankings(self):
        """
        checks with server in the background to see if ready to announce rankings
        """
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(config.CHANNEL_ID)

        while not self.bot.is_closed():
            rankings = await fetch_rankings()
            if rankings is None:
                await asyncio.sleep(60)
                continue

            # change return to {username: '...', scores: ['3/nmines', ...], order: ['asc', 'desc', ...]}
            username = rankings[0][0]
            scores = []
            for e in rankings:
                scores.append(str(e[2])+'/10')
            await channel.send(f"""
                        Minesweeper:
                {scores[0]}: <@{username}>

                        Simon Says:
                {scores[1]}: <@{username}>
            """)
            await asyncio.sleep(60)


    async def fetch_rankings(self):
        # use aiohttp instead of requests bc async lib
        async with aiohttp.ClientSession() as sesh:
            async with sesh.get(f"{self.API_URL}/rankings") as r:
                if r.status == 200:
                    data = await r.json()
                    return data['rankings']
        return None


# set up the cog
async def setup(bot):
    await bot.add_cog(Minigames(bot))

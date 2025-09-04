import asyncio
import aiohttp

import discord
from discord.ext import commands

import config


class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.API_URL = f'{config.BASE_URL}/api'
        # start background reminder loop
        self.bot.loop.create_task(self.announce_rankings())


    @commands.command(name="play")
    async def play(self, ctx):
        """
        Command format: !play
        """
        # use aiohttp instead of requests bc async lib
        async with aiohttp.ClientSession() as sesh:
            # remember to rm ssl=False once deployed
            async with sesh.get(f"{self.API_URL}/init_reset_time", ssl=False) as r:
                pass

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
        #await ctx.message.remove()


    async def announce_rankings(self):
        """
        checks with server in the background to see if ready to announce rankings
        """
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(config.CHANNEL_ID)
        if channel is None:
            channel = await self.bot.fetch_channel(config.CHANNEL_ID)

        while not self.bot.is_closed():
            rankings = await self.fetch_rankings()
            if rankings is None:
                await asyncio.sleep(20)
                continue

            await channel.send(f'{rankings}')
            '''await channel.send(f"""
                        Minesweeper:
                {scores[0]}: <@{username}>

                        Simon Says:
                {scores[1]}: <@{username}>
            """)
            '''
            await asyncio.sleep(20)


    async def fetch_rankings(self):
        async with aiohttp.ClientSession() as sesh:
            # remember to rm ssl=False once deployed
            async with sesh.get(f"{self.API_URL}/rankings", ssl=False) as r:
                if r.status == 200:
                    data = await r.json()
                    return data['rankings']
        return None


# set up the cog
async def setup(bot):
    await bot.add_cog(Minigames(bot))

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
        #await ctx.message.remove()  need right perms


    async def announce_rankings(self):
        """
        pings server every hour to see if ready to announce rankings
        """
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(config.CHANNEL_ID)
        if channel is None:
            channel = await self.bot.fetch_channel(config.CHANNEL_ID)

        while not self.bot.is_closed():
            data = await self.fetch_rankings()
            # 'not' covers both None and []
            if not data:
                await asyncio.sleep(10)
                continue

            rankings = data['rankings']
            max_scores = data['max_scores']
            streak = data['streak']

            await channel.send(f'standings: {rankings}\nmax scores: {max_scores}\ndaily streak: {streak}')
            await asyncio.sleep(10)


    # return: {rankings: {...}, max_scores: {game_id: str, max_score: int}, streak: int}
    async def fetch_rankings(self):
        async with aiohttp.ClientSession() as sesh:
            # remember to rm ssl=False once deployed
            async with sesh.get(f"{self.API_URL}/rankings", ssl=False) as r:
                if r.status == 200:
                    return await r.json()


# set up the cog
async def setup(bot):
    await bot.add_cog(Minigames(bot))

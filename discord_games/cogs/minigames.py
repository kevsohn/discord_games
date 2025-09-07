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
                name='',
                value=f"[Play Now]({config.BASE_URL})",
                inline=False
        )
        await ctx.reply(embed=embed)


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
                await asyncio.sleep(3600)
                continue

            # rankings already sorted
            rankings = data['rankings']
            max_scores = data['max_scores']
            streak = data['streak']

            msg = f'**Your group is on an {streak} day streak!** :fire: '
            msg += 'Here are yesterday\'s results:\n'
            last_rank = 0
            for r in rankings:
                game = r['game']
                max_score = max_scores[game]
                msg += f'{game.upper()}:\n'
                for player in r['players']:
                    score = player['score']
                    if last_rank == 0:
                        msg += f':crown: {score}/{max_score}: '
                        last_rank = 1

                    if player['rank'] == last_rank:
                        msg += f'<@{player['id']}> '
                    else:
                        msg += f'\n{score}/{max_score}: <@{player['id']}> '
                        last_rank += 1
                last_rank = 0
                msg += '\n\n'

            embed = discord.Embed(color=0x00ff00)
            embed.add_field(
                    name='',
                    value=f"[Play Now]({config.BASE_URL}/login)",
                    inline=False
            )

            await channel.send(msg, embed=embed)
            await asyncio.sleep(3600)


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

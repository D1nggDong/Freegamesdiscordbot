import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
from datetime import datetime
from typing import Optional

from .stores import EpicGamesStore, SteamStore
from .stores.base import FreeGame


class FreeGamesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        
        super().__init__(command_prefix="!", intents=intents)
        
        self.stores = [
            EpicGamesStore(),
            SteamStore()
        ]
        
        self.posted_games: set[tuple[str, str]] = set()
        self.notification_channel_id: Optional[int] = None
        self.ping_role_id: Optional[int] = None
        
        channel_id = os.getenv("DISCORD_CHANNEL_ID")
        if channel_id:
            self.notification_channel_id = int(channel_id)
        
        role_id = os.getenv("DISCORD_ROLE_ID")
        if role_id:
            self.ping_role_id = int(role_id)
    
    async def setup_hook(self):
        await self.add_cog(FreeGamesCog(self))
        await self.tree.sync()
        
        self.check_free_games.start()
    
    async def on_ready(self):
        print(f"Bot is ready! Logged in as {self.user}")
        print(f"Monitoring {len(self.stores)} stores for free games")
        if self.notification_channel_id:
            print(f"Notification channel ID: {self.notification_channel_id}")
        else:
            print("No notification channel set. Use /setchannel to configure.")
        
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Sharars Dih",
            state="Competitive",
            details="Finding 100% OFF deals"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    @tasks.loop(hours=1)
    async def check_free_games(self):
        if not self.notification_channel_id:
            return
        
        channel = self.get_channel(self.notification_channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            print(f"Could not find text channel {self.notification_channel_id}")
            return
        
        await self._check_and_post_games(channel)
    
    @check_free_games.before_loop
    async def before_check(self):
        await self.wait_until_ready()
        await asyncio.sleep(10)
    
    async def _check_and_post_games(self, channel: discord.TextChannel) -> list[FreeGame]:
        all_free_games = []
        
        for store in self.stores:
            try:
                games = await store.get_free_games()
                all_free_games.extend(games)
            except Exception as e:
                print(f"Error checking {store.name}: {e}")
        
        new_games = []
        for game in all_free_games:
            game_key = (game.title, game.store)
            if game_key not in self.posted_games:
                self.posted_games.add(game_key)
                new_games.append(game)
        
        for game in new_games:
            embed = self._create_game_embed(game)
            
            ping_text = ""
            if self.ping_role_id:
                ping_text = f"<@&{self.ping_role_id}> "
            
            await channel.send(content=f"{ping_text}🎮 **FREE GAME ALERT!**", embed=embed)
            await asyncio.sleep(1)
        
        return new_games
    
    def _create_game_embed(self, game: FreeGame) -> discord.Embed:
        if game.store == "Epic Games Store":
            color = discord.Color.from_rgb(0, 0, 0)
        elif game.store == "Steam":
            color = discord.Color.from_rgb(27, 40, 56)
        else:
            color = discord.Color.green()
        
        embed = discord.Embed(
            title=game.title,
            description=game.description,
            url=game.url,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(name=game.store)
        
        if game.image_url:
            embed.set_thumbnail(url=game.image_url)
        
        if game.original_price:
            embed.add_field(name="Original Price", value=f"~~{game.original_price}~~ → **FREE**", inline=True)
        else:
            embed.add_field(name="Price", value="**FREE (100% OFF)**", inline=True)
        
        if game.end_date:
            embed.add_field(
                name="Offer Ends",
                value=f"<t:{int(game.end_date.timestamp())}:R>",
                inline=True
            )
        
        embed.add_field(name="Claim Now", value=f"[Click Here]({game.url})", inline=False)
        
        embed.set_footer(text="Free Games Bot")
        
        return embed


class FreeGamesCog(commands.Cog):
    def __init__(self, bot: FreeGamesBot):
        self.bot = bot
    
    @app_commands.command(name="freegames", description="Check for current free games across all stores")
    async def free_games(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        all_games = []
        for store in self.bot.stores:
            try:
                games = await store.get_free_games()
                all_games.extend(games)
            except Exception as e:
                print(f"Error checking {store.name}: {e}")
        
        if not all_games:
            await interaction.followup.send("No free games found at the moment. Check back later!")
            return
        
        embed = discord.Embed(
            title="🎮 Current Free Games",
            description=f"Found {len(all_games)} free game(s)!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        for game in all_games[:10]:
            value = f"~~{game.original_price}~~ → FREE" if game.original_price else "FREE"
            if game.end_date:
                value += f"\nEnds <t:{int(game.end_date.timestamp())}:R>"
            value += f"\n[Claim Now]({game.url})"
            embed.add_field(name=f"{game.store}: {game.title}", value=value, inline=False)
        
        if len(all_games) > 10:
            embed.set_footer(text=f"Showing 10 of {len(all_games)} games")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="setchannel", description="Set the channel for free game notifications")
    @app_commands.default_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.bot.notification_channel_id = channel.id
        await interaction.response.send_message(
            f"✅ Notifications will be sent to {channel.mention}",
            ephemeral=True
        )
    
    @app_commands.command(name="setping", description="Set a role to ping for free game alerts")
    @app_commands.default_permissions(administrator=True)
    async def set_ping(self, interaction: discord.Interaction, role: discord.Role):
        self.bot.ping_role_id = role.id
        await interaction.response.send_message(
            f"✅ {role.mention} will be pinged for free game alerts",
            ephemeral=True
        )
    
    @app_commands.command(name="checknow", description="Force check for new free games now")
    @app_commands.default_permissions(administrator=True)
    async def check_now(self, interaction: discord.Interaction):
        if not self.bot.notification_channel_id:
            await interaction.response.send_message(
                "❌ No notification channel set. Use /setchannel first.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        channel = self.bot.get_channel(self.bot.notification_channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("❌ Could not find the notification channel.")
            return
        
        new_games = await self.bot._check_and_post_games(channel)
        
        if new_games:
            await interaction.followup.send(f"✅ Found and posted {len(new_games)} new free game(s)!")
        else:
            await interaction.followup.send("No new free games found since last check.")
    
    @app_commands.command(name="status", description="Show bot status and configuration")
    async def status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Free Games Bot Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        stores_list = "\n".join([f"• {store.name}" for store in self.bot.stores])
        embed.add_field(name="Monitored Stores", value=stores_list, inline=False)
        
        if self.bot.notification_channel_id:
            channel = self.bot.get_channel(self.bot.notification_channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                channel_text = channel.mention
            else:
                channel_text = f"ID: {self.bot.notification_channel_id}"
        else:
            channel_text = "Not set"
        embed.add_field(name="Notification Channel", value=channel_text, inline=True)
        
        if self.bot.ping_role_id:
            ping_text = f"<@&{self.bot.ping_role_id}>"
        else:
            ping_text = "None"
        embed.add_field(name="Ping Role", value=ping_text, inline=True)
        
        embed.add_field(name="Check Interval", value="Every 1 hour", inline=True)
        embed.add_field(name="Games Posted", value=str(len(self.bot.posted_games)), inline=True)
        
        await interaction.response.send_message(embed=embed)

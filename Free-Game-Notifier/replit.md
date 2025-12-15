# Free Games Discord Bot

## Overview
A Python Discord bot that monitors game stores (Epic Games Store, Steam) for 100% off deals and posts notifications to a Discord channel with role pings.

## Project Structure
```
├── main.py                    # Entry point
├── src/
│   ├── __init__.py
│   ├── bot.py                 # Discord bot with commands and monitoring
│   └── stores/
│       ├── __init__.py
│       ├── base.py            # Base store class and FreeGame dataclass
│       ├── epic_games.py      # Epic Games Store integration
│       └── steam.py           # Steam Store integration
```

## Features
- Monitors Epic Games Store and Steam for free games
- Automatic hourly checks for new deals
- Rich Presence status showing "Watching for free games 🎮"
- Discord slash commands:
  - `/freegames` - List all current free games
  - `/setchannel` - Set notification channel (admin only)
  - `/setping` - Set role to ping (admin only)
  - `/checknow` - Force immediate check (admin only)
  - `/status` - Show bot status and configuration

## Required Secrets
- `DISCORD_BOT_TOKEN` - Your Discord bot token (required)
- `DISCORD_CHANNEL_ID` - Channel ID for notifications (optional, can use /setchannel)
- `DISCORD_ROLE_ID` - Role ID to ping (optional, can use /setping)

## Setup Instructions
1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and copy the token
3. Add `DISCORD_BOT_TOKEN` to Secrets
4. Invite bot to your server with these permissions:
   - Send Messages
   - Embed Links
   - Mention Everyone (for role pings)
   - Use Slash Commands

## Running the Bot
Run `python main.py` to start the bot.

## Technical Details
- Uses discord.py for Discord integration
- Uses aiohttp for async HTTP requests
- Uses BeautifulSoup for Steam web scraping
- Checks for new games every hour
- Tracks posted games to prevent duplicates (in-memory)

## Recent Changes
- December 15, 2025: Added Rich Presence status display
- December 15, 2025: Initial implementation with Epic Games and Steam support

import os
from dotenv import load_dotenv
from src.bot import FreeGamesBot

load_dotenv()

def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    
    if not token:
        print("=" * 50)
        print("ERROR: DISCORD_BOT_TOKEN not found!")
        print("=" * 50)
        print("\nTo set up the bot:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Create a new application or select existing one")
        print("3. Go to 'Bot' section and copy the token")
        print("4. Add DISCORD_BOT_TOKEN to your Secrets")
        print("\nOptional environment variables:")
        print("- DISCORD_CHANNEL_ID: Channel ID for notifications")
        print("- DISCORD_ROLE_ID: Role ID to ping for alerts")
        print("=" * 50)
        return
    
    bot = FreeGamesBot()
    bot.run(token)

if __name__ == "__main__":
    main()

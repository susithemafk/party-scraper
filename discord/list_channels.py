"""Simple helper to list every channel in the servers the bot can see."""

from dotenv import load_dotenv
import discord
import os


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise SystemExit("DISCORD_TOKEN was not found in the environment."
                     " Add it to your .env before running this script.")

intents = discord.Intents.none()
intents.guilds = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Connected as {client.user} ({client.user.id})\n")
    for guild in client.guilds:
        print(f"{guild.name} ({guild.id})")
        print("Channels:")
        for channel in guild.channels:
            print(f"  - {channel.name} (ID: {channel.id}) [{channel.type.name}]")
        print()
    await client.close()


def main():
    try:
        client.run(TOKEN)
    except discord.LoginFailure:
        raise SystemExit("Discord rejected the token. Verify DISCORD_TOKEN in your .env.")


if __name__ == "__main__":
    main()
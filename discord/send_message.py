"""Send a single message to a Discord channel identified by ID."""

import os

import discord
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
MESSAGE = os.getenv("TARGET_MESSAGE", "Hello from the party scraper bot!")

if not TOKEN:
    raise SystemExit("DISCORD_TOKEN is missing from the .env file.")

if not CHANNEL_ID:
    raise SystemExit("TARGET_CHANNEL_ID is missing from the .env file.")

try:
    channel_id = int(CHANNEL_ID)
except ValueError:
    raise SystemExit("TARGET_CHANNEL_ID must be a valid integer.")

intents = discord.Intents.none()
intents.guilds = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    channel = client.get_channel(channel_id)
    if channel is None:
        raise SystemExit(f"Channel {channel_id} was not found.")

    sent = await channel.send(MESSAGE)
    print(f"Sent message (ID: {sent.id}) to {channel.guild.name} / {channel.name}.")
    await client.close()


def main():
    try:
        client.run(TOKEN)
    except discord.LoginFailure:
        raise SystemExit("Discord rejected the token. Revisit DISCORD_TOKEN in .env.")


if __name__ == "__main__":
    main()
import discord
import logging
import json

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)

discord_token = config["discord_token"]


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))


client = MyClient()
client.run(discord_token)
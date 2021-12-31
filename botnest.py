import discord
import logging
import json
import anilist_api

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)

discord_token = config["discord_token"]


class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        channel = client.get_channel(config["channel_id"])

        # remove previous bot messages
        await channel.purge(check=lambda m: m.author == client.user)

        data = anilist_api.get_anime_list()
        # pretty print
        # data = json.dumps(data, indent=2, ensure_ascii=False)

        # stats printout
        output = ""
        for list in data["data"]["MediaListCollection"]["lists"]:
            output += list["name"] + ": \n\n"
            for anime in list["entries"]:
                anime = anime["media"]
                output += "\n".join([title for title in anime["title"].values()]) + "\n"
                output += f"{anime['episodes']} episodes, average {anime['duration']}min\n"
                hours = anime['episodes'] * anime['duration'] / 60
                hours = format(hours, '.1f')
                output += f"{hours} hours total\n\n"

        await channel.send(f"```\n{output}```")

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))
        if message.author == client.user:
            return

        if message.content.startswith('!channel_id'):
            await message.channel.send(message.channel.id)


client = MyClient()
client.run(discord_token)
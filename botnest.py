import discord
import logging
import json
import anilist_api

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)

discord_token = config["discord_token"]
in_progress = {}

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
        watching = None
        total_hours = 0
        username = data["data"]["MediaListCollection"]["user"]["name"]
        user_url = data["data"]["MediaListCollection"]["user"]["siteUrl"]
        embed = discord.Embed(title=username, url=user_url, color=0x00ff00)
        for list in data["data"]["MediaListCollection"]["lists"]:
            # saving anime in progress
            if list["name"] == "Watching":
                watching = list["entries"]

            # general stats display
            for anime in list["entries"]:
                anime = anime["media"]
                hours = anime['episodes'] * anime['duration'] / 60
                total_hours += hours

        total_hours = format(total_hours, ".1f")
        embed.add_field(name="Total hours watched", value=total_hours)
        await channel.send(embed=embed)

        # individual anime in progress
        if watching:
            for anime in watching:
                progress = anime["progress"]
                anime = anime["media"]
                progress_str = f"{progress}/{anime['episodes']}"
                title = f"{anime['title']['native']}\n{anime['title']['english']}"
                desc = f"{anime['description'][:300]}..."
                color = int(anime["coverImage"]["color"][1:], 16)
                embed = discord.Embed(title=title, description=desc, url=anime["siteUrl"], color=color) # 0x00ff00
                embed.add_field(name="Progress: ", value=progress_str)
                embed.set_thumbnail(url=anime["coverImage"]["extraLarge"])
                in_progress[embed] = {"id": anime["id"], "progress": progress}
                await channel.send(embed=embed)

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))
        if message.author == client.user:
            return

        if message.content.startswith('!channel_id'):
            await message.channel.send(message.channel.id)


client = MyClient()
client.run(discord_token)
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
        watching = None
        for list in data["data"]["MediaListCollection"]["lists"]:
            # saving anime in progress
            if list["name"] == "Watching":
                watching = list["entries"]

            # general stats display
            output += list["name"] + ": \n\n"
            for anime in list["entries"]:
                anime = anime["media"]
                output += "\n".join([title for title in anime["title"].values()]) + "\n"
                output += f"{anime['episodes']} episodes, average {anime['duration']}min\n"
                hours = anime['episodes'] * anime['duration'] / 60
                hours = format(hours, '.1f')
                output += f"{hours} hours total\n\n"

        await channel.send(f"```\n{output}```")

        # individual anime in progress
        if watching:
            for anime in watching:
                progress = str(anime["progress"])
                anime = anime["media"]
                progress += "/" + str(anime["episodes"])
                title = f"{anime['title']['english']} / {anime['title']['native']}"
                desc = f"{anime['description'][:300]}..."
                # await channel.send(f"```\n{json.dumps(anime, indent=2, ensure_ascii=False)}```")
                embed = discord.Embed(title=title, description=desc, color=0x00ff00)
                # embed.set_author(name="icon", icon_url=anime["coverImage"]["extraLarge"])
                embed.add_field(name="Progress: ", value=progress, inline=True)
                # embed.add_field(name="Field1", value="hi", inline=False)
                # embed.add_field(name="Field2", value="hi2", inline=False)
                await channel.send(embed=embed)

    async def on_message(self, message):
        print("Message from {0.author}: {0.content}".format(message))
        if message.author == client.user:
            return

        if message.content.startswith('!channel_id'):
            await message.channel.send(message.channel.id)


client = MyClient()
client.run(discord_token)
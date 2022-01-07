import discord
import logging
import json
import anilist_api

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)

discord_token = config["discord_token"]
in_progress = {}
default_reacts = ["⬆️", "⬇️", "⏸️", "❌"]

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged on as {client.user}!")
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
            hours = 0
            if anime["status"] in ["COMPLETED", "REPEATING"]:
                hours = anime["media"]['episodes'] * anime["media"]['duration'] / 60
            elif anime["status"] in ["CURRENT", "PAUSED", "DROPPED"]:
                hours = anime["progress"] * anime["media"]['duration'] / 60
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
            message = await channel.send(embed=embed)
            for emoji in default_reacts:
                await message.add_reaction(emoji)
            in_progress[message] = {"id": anime["id"], "progress": progress, "name": anime['title']['native']}


@client.event
async def on_message(message):
    print(f"Message from {message.author}: {message.content}")
    if message.author == client.user:
        return

    if message.content.startswith('!channel_id'):
        await message.channel.send(message.channel.id)


@client.event
async def on_reaction_add(reaction, user):
    await process_reaction(reaction, user)


@client.event
async def on_reaction_remove(reaction, user):
    await process_reaction(reaction, user)


async def process_reaction(reaction, user):
    if user == client.user or reaction.message not in in_progress or reaction not in default_reacts:
        return
    anime = in_progress[reaction.message]
    print(f"{user} reacted with {reaction} ({reaction.emoji}) on this message:")
    print(f"{anime['name']}: {anime['progress']}")


client.run(discord_token)
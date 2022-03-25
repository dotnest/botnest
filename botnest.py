import discord
import logging
import json
import anilist_api
import re

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)

discord_token = config["discord_token"]
in_progress = {}
default_reacts = {"⬆️": "increase", "⬇️": "decrease", "⏸️": "pause", "❌": "drop"}

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    async def process_anime():
        data = await anilist_api.get_anime_list()
        # pretty print
        # data = json.dumps(data, indent=2, ensure_ascii=False)

        # stats printout
        watching = None
        total_hours = 0
        username = data["data"]["MediaListCollection"]["user"]["name"]
        user_url = data["data"]["MediaListCollection"]["user"]["siteUrl"]
        embed = discord.Embed(title=username, url=user_url, color=0x00FF00)
        for list in data["data"]["MediaListCollection"]["lists"]:
            # saving anime in progress
            if list["name"] == "Watching":
                watching = list["entries"]

            # general stats display
            for anime in list["entries"]:
                hours = 0
                if anime["status"] in ["COMPLETED", "REPEATING"]:
                    hours = anime["media"]["episodes"] * anime["media"]["duration"] / 60
                elif anime["status"] in ["CURRENT", "PAUSED", "DROPPED"]:
                    hours = anime["progress"] * anime["media"]["duration"] / 60
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
                desc = re.sub("<.*?>", "", anime["description"])
                desc = f"{desc[:300]}..."
                if anime["coverImage"]["color"]:
                    color = int(anime["coverImage"]["color"][1:], 16)
                else:
                    color = 0x00FF00
                embed = discord.Embed(
                    title=title, description=desc, url=anime["siteUrl"], color=color
                )
                embed.add_field(name="Progress: ", value=progress_str)
                embed.set_thumbnail(url=anime["coverImage"]["extraLarge"])
                message = await channel.send(embed=embed)
                in_progress[message] = {
                    "type": "anime",
                    "id": anime["id"],
                    "progress": progress,
                    "total": anime["episodes"],
                    "name": anime["title"]["native"],
                }
                for emoji in default_reacts:
                    await message.add_reaction(emoji)

    async def process_manga():
        data = await anilist_api.get_manga_list()
        # pretty print
        # data = json.dumps(data, indent=2, ensure_ascii=False)

        # stats printout
        reading = None
        total_chapters = 0
        username = data["data"]["MediaListCollection"]["user"]["name"]
        user_url = data["data"]["MediaListCollection"]["user"]["siteUrl"]
        embed = discord.Embed(title=username, url=user_url, color=0x00FF00)
        for list in data["data"]["MediaListCollection"]["lists"]:
            # saving manga in progress
            if list["name"] == "Reading":
                reading = list["entries"]

            # general stats display
            for manga in list["entries"]:
                chapters = 0
                if manga["status"] in ["COMPLETED", "REPEATING"]:
                    chapters = manga["media"]["chapters"]
                elif manga["status"] in ["CURRENT", "PAUSED", "DROPPED"]:
                    chapters = manga["progress"]
                total_chapters += chapters

        embed.add_field(name="Total chapters read", value=total_chapters)
        await channel.send(embed=embed)

        # individual manga in progress
        if reading:
            for manga in reading:
                progress = manga["progress"]
                manga = manga["media"]
                # because manga chapters/volumes are sometimes null
                if manga["chapters"]:
                    progress_str = f"{progress}/{manga['chapters']}"
                else:
                    progress_str = f"{progress}"
                title = f"{manga['title']['native']}\n{manga['title']['english']}"
                desc = re.sub("<.*?>", "", manga["description"])
                desc = f"{desc[:300]}..."
                if manga["coverImage"]["color"]:
                    color = int(manga["coverImage"]["color"][1:], 16)
                else:
                    color = 0x00FF00
                embed = discord.Embed(
                    title=title, description=desc, url=manga["siteUrl"], color=color
                )
                embed.add_field(name="Progress: ", value=progress_str)
                embed.set_thumbnail(url=manga["coverImage"]["extraLarge"])
                message = await channel.send(embed=embed)
                in_progress[message] = {
                    "type": "manga",
                    "id": manga["id"],
                    "progress": progress,
                    "total": manga["chapters"],
                    "name": manga["title"]["native"],
                }
                for emoji in default_reacts:
                    await message.add_reaction(emoji)

    print(f"Logged on as {client.user}!")
    try:
        channel = client.get_channel(int(config["channel_id"]))
    except:
        print("Couldn't get channel id from config")
        print("Get one by typing '!channel_id' in channel you want your bot in")
        return

    # remove previous bot messages
    await channel.purge(check=lambda m: m.author == client.user)

    await process_anime()
    await process_manga()


@client.event
async def on_message(message):
    print(f"Message from {message.author}: {message.content}")
    if message.author == client.user:
        return

    if message.content.startswith("!channel_id"):
        await message.channel.send(message.channel.id)

    if message.content == "!r":
        await message.delete()
        await on_ready()


@client.event
async def on_reaction_add(reaction, user):
    await process_reaction(reaction, user)


@client.event
async def on_reaction_remove(reaction, user):
    await process_reaction(reaction, user)


async def process_reaction(reaction, user):
    if (
        user == client.user
        or reaction.message not in in_progress
        or reaction.emoji not in default_reacts
    ):
        return
    media = in_progress[reaction.message]
    print(f"{user} reacted with {reaction} ({reaction.emoji}) on this message:")
    print(f"{media['name']}: {media['progress']}/{media['total']}")

    action = default_reacts[reaction.emoji]
    if action == "increase":
        if media["total"] and media["progress"] + 1 >= media["total"]:
            # update on website
            await anilist_api.update_media(
                media["id"], "COMPLETED", media["progress"] + 1
            )
            # delete embed
            await reaction.message.delete()
            # delete from memory
            del in_progress[reaction.message]
        else:
            # update on website
            await anilist_api.update_media(
                media["id"], "CURRENT", media["progress"] + 1
            )
            # update embed
            embed = reaction.message.embeds[0]
            embed = embed.to_dict()
            # because manga chapters/volumes are sometimes null
            if media["total"]:
                embed["fields"][0]["value"] = f"{media['progress']+1}/{media['total']}"
            else:
                embed["fields"][0]["value"] = f"{media['progress']+1}"
            embed = discord.Embed.from_dict(embed)
            await reaction.message.edit(embed=embed)
            # update in memory
            in_progress[reaction.message]["progress"] += 1
    elif action == "decrease":
        if media["progress"] == 0:
            return

        # update on website
        await anilist_api.update_media(media["id"], "CURRENT", media["progress"] - 1)
        # update embed
        embed = reaction.message.embeds[0]
        embed = embed.to_dict()
        # because manga chapters/volumes are sometimes null
        if media["total"]:
            embed["fields"][0]["value"] = f"{media['progress']-1}/{media['total']}"
        else:
            embed["fields"][0]["value"] = f"{media['progress']-1}"
        embed = discord.Embed.from_dict(embed)
        await reaction.message.edit(embed=embed)
        # update in memory
        in_progress[reaction.message]["progress"] -= 1
    elif action in ["pause", "drop"]:
        if action == "pause":
            status = "PAUSED"
        else:
            status = "DROPPED"
        # update on website
        await anilist_api.update_media(media["id"], status, media["progress"])
        # delete embed
        await reaction.message.delete()
        # delete from memory
        del in_progress[reaction.message]


client.run(discord_token)

# TODO: youtube playlist support? with links to open on mobile/jidoujisho
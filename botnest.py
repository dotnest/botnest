import discord
import logging
import json
import anilist_api
import re
import pytube

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)

discord_token = config["discord_token"]
in_progress = {}
default_reacts = {"⬆️": "increase", "⬇️": "decrease", "⏸️": "pause", "❌": "drop"}

intents = discord.Intents.all()
client = discord.Client(intents=intents)

playlists = config["youtube_playlists"]
playlist_reacts = {"⬆️": "increase", "⬇️": "decrease", "❌": "drop"}


@client.event
async def on_ready():
    async def process_anime(channel):
        data = await anilist_api.get_anime_list()

        # stats printout
        watching = []
        total_hours = 0
        username = config["username"]
        user_url = f"https://anilist.co/user/{username}"
        embed = discord.Embed(title=username, url=user_url, color=0x00FF00)
        for anime in data:
            # saving anime in progress
            if anime.status == "CURRENT":
                watching.append(anime)

            # general stats display
            hours = 0
            if anime.status in ["COMPLETED", "REPEATING"]:
                hours = anime.total * anime.duration / 60
            elif anime.status in ["CURRENT", "PAUSED", "DROPPED"]:
                hours = anime.progress * anime.duration / 60
            total_hours += hours

        total_hours = format(total_hours, ".1f")
        embed.add_field(name="Total hours watched", value=total_hours)
        await channel.send(embed=embed)

        # individual anime in progress
        if len(watching) > 0:
            for anime in watching:
                progress_str = f"{anime.progress}/{anime.total}"
                title = f"{anime.title_jp}\n{anime.title_en}"
                desc = re.sub("<.*?>", "", anime.description)
                desc = f"{desc[:300]}..."
                if anime.color:
                    color = int(anime.color[1:], 16)
                else:
                    color = 0x00FF00
                embed = discord.Embed(
                    title=title, description=desc, url=anime.site_url, color=color
                )
                embed.add_field(name="Progress: ", value=progress_str)
                embed.set_thumbnail(url=anime.cover_image)
                message = await channel.send(embed=embed)
                in_progress[message] = anime
                for emoji in default_reacts:
                    await message.add_reaction(emoji)

    async def process_manga(channel):
        data = await anilist_api.get_manga_list()

        # stats printout
        reading = []
        total_chapters = 0
        username = config["username"]
        user_url = f"https://anilist.co/user/{username}"
        embed = discord.Embed(title=username, url=user_url, color=0x00FF00)
        for manga in data:
            # saving manga in progress
            if manga.status == "CURRENT":
                reading.append(manga)

            # general stats display
            chapters = 0
            if manga.status in ["COMPLETED", "REPEATING"]:
                chapters = manga.total
            elif manga.status in ["CURRENT", "PAUSED", "DROPPED"]:
                chapters = manga.progress
            total_chapters += chapters

        embed.add_field(name="Total chapters read", value=total_chapters)
        await channel.send(embed=embed)

        # individual manga in progress
        if len(reading) > 0:
            for manga in reading:
                # because manga chapters/volumes are sometimes null
                if manga.total:
                    progress_str = f"{manga.progress}/{manga.total}"
                else:
                    progress_str = f"{manga.progress}"
                title = f"{manga.title_jp}\n{manga.title_en}"
                desc = re.sub("<.*?>", "", manga.description)
                desc = f"{desc[:300]}..."
                if manga.color:
                    color = int(manga.color[1:], 16)
                else:
                    color = 0x00FF00
                embed = discord.Embed(
                    title=title, description=desc, url=manga.site_url, color=color
                )
                embed.add_field(name="Progress: ", value=progress_str)
                embed.set_thumbnail(url=manga.cover_image)
                message = await channel.send(embed=embed)
                in_progress[message] = manga
                for emoji in default_reacts:
                    await message.add_reaction(emoji)

    async def process_playlists(channel):
        for playlist_url, index in playlists.items():
            playlist = pytube.Playlist(playlist_url)
            # because pytube throws an exception if there's no description
            try:
                description = playlist.description
            except:
                description = ""
            embed = discord.Embed(
                title=playlist.title, description=description, url=playlist_url
            )
            next_video = playlist.videos[index]
            url = playlist.video_urls[index]
            embed.add_field(name="Next video:", value=f"[{next_video.title}]({url})")
            embed.set_thumbnail(url=next_video.thumbnail_url)
            message = await channel.send(embed=embed)
            in_progress[message] = {
                "type": "playlist",
                "index": index,
                "playlist_url": playlist_url,
                "playlist": playlist,
            }
            for emoji in playlist_reacts:
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

    await process_anime(channel)
    await process_manga(channel)
    await process_playlists(channel)


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

    if message.channel.id == int(config["channel_id"]) and (
        "youtube.com" in message.content or "youtu.be" in message.content
    ):
        try:
            playlist = pytube.Playlist(message.content)
            if "index=" in message.content:
                index = int(message.content.split("index=")[1])
            else:
                video_url = pytube.YouTube(message.content).watch_url
                if "https://www.youtube" not in video_url:
                    # because pytube
                    video_url = video_url.replace("https://you", "https://www.you")
                if video_url in playlist.video_urls:
                    index = list(playlist.video_urls).index(video_url)
                else:
                    index = 0
            await message.delete()
            print("got index", index)
            # saving in memory
            playlists[playlist.playlist_url] = index
            config["youtube_playlists"] = playlists
            # saving in config
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print("Couldn't load youtube link")
            print(e)


@client.event
async def on_reaction_add(reaction, user):
    await process_reaction(reaction, user)


@client.event
async def on_reaction_remove(reaction, user):
    await process_reaction(reaction, user)


async def process_reaction(reaction, user):
    async def process_media(reaction, media, action):
        if action == "increase":
            if media.total and media.progress + 1 >= media.total:
                # update on website
                await anilist_api.update_media(
                    media.id, "COMPLETED", media.progress + 1
                )
                # delete embed
                await reaction.message.delete()
                # delete from memory
                del in_progress[reaction.message]
            else:
                # update on website
                await anilist_api.update_media(media.id, "CURRENT", media.progress + 1)
                # update embed
                embed = reaction.message.embeds[0]
                embed = embed.to_dict()
                # to see embed structure:
                # with open("dev_embed.json", "w") as f:
                #     json.dump(embed, f, indent=4)
                # because manga chapters/volumes are sometimes null
                if media.total:
                    embed["fields"][0]["value"] = f"{media.progress+1}/{media.total}"
                else:
                    embed["fields"][0]["value"] = f"{media.progress+1}"
                embed = discord.Embed.from_dict(embed)
                await reaction.message.edit(embed=embed)
                # update in memory
                in_progress[reaction.message].progress += 1
        elif action == "decrease":
            if media.progress == 0:
                return

            # update on website
            await anilist_api.update_media(media.id, "CURRENT", media.progress - 1)
            # update embed
            embed = reaction.message.embeds[0]
            embed = embed.to_dict()
            # because manga chapters/volumes are sometimes null
            if media.total:
                embed["fields"][0]["value"] = f"{media.progress-1}/{media.total}"
            else:
                embed["fields"][0]["value"] = f"{media.progress-1}"
            embed = discord.Embed.from_dict(embed)
            await reaction.message.edit(embed=embed)
            # update in memory
            in_progress[reaction.message].progress -= 1
        elif action in ["pause", "drop"]:
            if action == "pause":
                status = "PAUSED"
            else:
                status = "DROPPED"
            # update on website
            await anilist_api.update_media(media.id, status, media.progress)
            # delete embed
            await reaction.message.delete()
            # delete from memory
            del in_progress[reaction.message]

    async def process_playlist(reaction, media, action):
        playlist = media["playlist"]
        index = media["index"]
        playlist_url = media["playlist_url"]
        if action == "increase":
            if index + 1 >= playlist.length:
                # delete from config
                del playlists[playlist_url]
                config["youtube_playlists"] = playlists
                with open("config.json", "w") as f:
                    json.dump(config, f, indent=4)
                # delete embed
                await reaction.message.delete()
                # delete from memory
                del in_progress[reaction.message]
            else:
                # update in config
                playlists[playlist_url] += 1
                config["youtube_playlists"] = playlists
                with open("config.json", "w") as f:
                    json.dump(config, f, indent=4)
                # update embed
                embed = reaction.message.embeds[0]
                embed = embed.to_dict()
                # to see embed structure:
                # with open("dev_embed.json", "w") as f:
                #     json.dump(embed, f, indent=4)
                next_video = playlist.videos[index + 1]
                url = playlist.video_urls[index + 1]
                embed["fields"][0]["value"] = f"[{next_video.title}]({url})"
                embed = discord.Embed.from_dict(embed)
                await reaction.message.edit(embed=embed)
                # update in memory
                in_progress[reaction.message]["index"] += 1
        elif action == "decrease":
            if index == 0:
                return

            # update in config
            playlists[playlist_url] -= 1
            config["youtube_playlists"] = playlists
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            # update embed
            embed = reaction.message.embeds[0]
            embed = embed.to_dict()
            prev_video = playlist.videos[index - 1]
            url = playlist.video_urls[index - 1]
            embed["fields"][0]["value"] = f"[{prev_video.title}]({url})"
            embed = discord.Embed.from_dict(embed)
            await reaction.message.edit(embed=embed)
            # update in memory
            in_progress[reaction.message]["index"] -= 1
        elif action == "drop":
            # delete from config
            del playlists[playlist_url]
            config["youtube_playlists"] = playlists
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            # delete embed
            await reaction.message.delete()
            # delete from memory
            del in_progress[reaction.message]

    # ignoring unwanted reactions
    if (
        user == client.user
        or reaction.message not in in_progress
        or reaction.emoji not in default_reacts
    ):
        return

    media = in_progress[reaction.message]
    action = default_reacts[reaction.emoji]
    print(f"{user} reacted with {reaction} ({reaction.emoji})")

    if isinstance(media, anilist_api.media.Media):
        # processing anime and manga
        await process_media(reaction, media, action)
    elif isinstance(media, dict) and media["type"] == "playlist":
        # processing youtube playlists
        await process_playlist(reaction, media, action)


client.run(discord_token)

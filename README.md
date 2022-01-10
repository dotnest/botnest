# botnest
This bot allows you to track and update your immersion progress on [Anilist](https://anilist.co/home) straight from your own discord server. Just click on a reaction under the message!

![](example.png)

## Requirements
- [Python 3.8+](https://www.python.org/downloads/)
- [Pycord](https://github.com/Pycord-Development/pycord) (maintained fork of [discord.py](https://github.com/Rapptz/discord.py))
- [Discord bot account](https://docs.pycord.dev/en/master/discord.html)
- [Anilist API access](https://anilist.gitbook.io/anilist-apiv2-docs/overview/oauth/getting-started)

## Preparations
- [Download](https://github.com/dotnest/botnest/archive/refs/heads/main.zip) and unpack this repository
- Create a `config.json` file and paste the following inside
```json
{
    "discord_token": "your discord bot token here",
    "access_token": "your anilist access token here",
    "refresh_token": "your anilist refresh token here",
    "user_name": "your anilist username here",
    "channel_id": "your channel id here"
}
```
- Put in your discord bot token, Anilist's access and refresh tokens and Anilist username
- Run the bot, type `!channel_id` in the channel where you want your tracking information to be
- Put that id in your config, restart the bot

## Available commands
- `!r` - resyncs with Anilist
- `!channel_id` - prints out current channel id
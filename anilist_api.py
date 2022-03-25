import requests
import json
import aiohttp

with open("config.json") as f:
    config = json.load(f)

access_token = config["access_token"]
user_name = config["user_name"]

url = "https://graphql.anilist.co"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


async def update_media(id, status, progress):
    query = """
    mutation ($mediaId: Int, $status: MediaListStatus, $progress: Int) {
        SaveMediaListEntry (mediaId: $mediaId, status: $status, progress: $progress) {
            id
            status
            progress
        }
    }
    """

    variables = {"mediaId": id, "status": status, "progress": progress}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"query": query, "variables": variables}, headers=headers
        ) as r:
            print(r.status)
            if r.status == 200:
                data = await r.json()
                print(data)
            else:
                print(r)


async def get_anime_list():
    """Return a dict of all user's registered anime"""
    query = """
    query ($userName: String) {
        MediaListCollection (userName: $userName, type: ANIME) {
            user {
                id
                name
                siteUrl
            }
            lists {
                name
                entries {
                    status
                    progress
                    media {
                        id
                        idMal
                        title {
                            english
                            native
                        }
                        description
                        coverImage {
                            extraLarge
                            color
                        }
                        siteUrl
                        episodes
                        duration
                    }
                }
            }
        }
    }
    """

    variables = {"userName": user_name}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"query": query, "variables": variables}, headers=headers
        ) as r:
            print(r.status)
            if r.status == 200:
                data = await r.json()

                with open("dev_anijson.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)

                return data
            else:
                print(r)


async def get_manga_list():
    """Return a dict of all user's registered manga"""
    query = """
    query ($userName: String) {
        MediaListCollection (userName: $userName, type: MANGA) {
            user {
                id
                name
                siteUrl
            }
            lists {
                name
                entries {
                    status
                    progress
                    media {
                        id
                        idMal
                        title {
                            english
                            native
                        }
                        description
                        coverImage {
                            extraLarge
                            color
                        }
                        siteUrl
                        chapters
                        volumes
                    }
                }
            }
        }
    }
    """

    variables = {"userName": user_name}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"query": query, "variables": variables}, headers=headers
        ) as r:
            print(r.status)
            if r.status == 200:
                data = await r.json()

                with open("dev_anijson.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)

                return data
            else:
                print(r)
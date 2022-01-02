import requests
import json

with open("config.json") as f:
    config = json.load(f)

access_token = config["access_token"]
user_id = config["user_id"]
user_name = config["user_name"]

url = "https://graphql.anilist.co"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def update_anime():
    query = """
    mutation ($mediaId: Int, $status: MediaListStatus, $progress: Int) {
        SaveMediaListEntry (mediaId: $mediaId, status: $status, progress: $progress) {
            id
            status
            progress
        }
    }
    """

    variables = {"mediaId": 1, "status": "CURRENT", "progress": 5}

    response = requests.post(
        url, json={"query": query, "variables": variables}, headers=headers
    )
    data = json.loads(response.text)
    print(data)

def get_anime_list():
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
                        title {
                            english
                            native
                        }
                        description
                        coverImage {
                            extraLarge
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

    response = requests.post(
        url, json={"query": query, "variables": variables}, headers=headers
    )
    data = json.loads(response.text)
    print(data)

    with open("dev_anijson.json", "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    return data

get_anime_list()
# add a stats screen, with total amount of episodes watched, hours watched
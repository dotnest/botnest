import webbrowser
import requests
import json

redirect_uri = "https://anilist.co/api/v2/oauth/pin"

client_id = "a"
while not client_id.isnumeric():
    client_id = input("Your client id: ")
    if not client_id.isnumeric():
        print("Incorrect ID, try again. It should be a number")

client_id = int(client_id)

client_secret = input("Your client secret: ")

target_url = f"https://anilist.co/api/v2/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"

webbrowser.open(target_url)

code = input("Your Authentication code from browser window: ")

data = requests.post(
    "https://anilist.co/api/v2/oauth/token",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    json={
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    },
)

with open("api.json", "w") as f:
    data = json.loads(data.text)
    json.dump(data, f)
    print("Successfully written tokens to api.json")
    input("Press Enter to finish...")
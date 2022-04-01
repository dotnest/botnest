class Media:
    def __init__(self, entry) -> None:
        self.status = entry["status"]
        self.progress = entry["progress"]
        self.id = entry["media"]["id"]
        self.idMal = entry["media"]["idMal"]
        self.title_en = entry["media"]["title"]["english"]
        self.title_jp = entry["media"]["title"]["native"]
        self.description = entry["media"]["description"]
        self.cover_image = entry["media"]["coverImage"]["extraLarge"]
        self.color = entry["media"]["coverImage"]["color"]
        self.site_url = entry["media"]["siteUrl"]
        self.total = entry["media"]["episodes"]
        self.duration = entry["media"]["duration"]

    def __repr__(self) -> str:
        return self.title_jp

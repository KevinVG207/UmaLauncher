import requests
class class1:
    classvar = 1

    r = requests.get("https://discord.com/api/v9/oauth2/applications/954453106765225995/assets")
    print("a")
    available_chara_icons = []
    if r.ok:
        assets = r.json()
        available_chara_icons = [
            asset['name']
            for asset in assets
            if asset['name'].startswith("chara_")
        ]

    def add(self):
        self.classvar += 1

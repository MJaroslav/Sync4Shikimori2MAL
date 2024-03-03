from sync4s2m import logger
from sync4s2m.auth import ShikimoriAPIManager, MyAnimeListAPIManager

import requests


shikimori_api = ShikimoriAPIManager()
shikimori_api.login()


result = shikimori_api.client.get(f"https://shikimori.one/api/users/{shikimori_api.whoami['id']}/anime_rates", params={"limit": 5000}).json()
result = [e["anime"]["russian"] for e in result]
print(result)



myanimelist_api = MyAnimeListAPIManager()
myanimelist_api.login()

result = myanimelist_api.client.get("https://api.myanimelist.net/v2/users/@me/animelist", params={"limit": 1000}).json()
result = [e["node"]["title"] for e in result["data"]]
print(result)


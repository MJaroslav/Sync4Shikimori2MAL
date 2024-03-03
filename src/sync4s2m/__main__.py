from sync4s2m import logger
from sync4s2m.auth import ShikimoriAPIManager, MyAnimeListAPIManager

import requests


shikimori_api = ShikimoriAPIManager()
shikimori_api.login()


result = shikimori_api.client.get(f"https://shikimori.one/api/users/{shikimori_api.whoami['id']}/anime_rates", params={"limit": 5000}).json()
sresult = {e["anime"]["id"]: e["anime"]["name"] for e in result}



myanimelist_api = MyAnimeListAPIManager()
myanimelist_api.login()

result = myanimelist_api.client.get("https://api.myanimelist.net/v2/users/@me/animelist", params={"limit": 1000}).json()
mresult = {e["node"]["id"]: e["node"]["title"] for e in result["data"]}


result = {sid: [sname, mresult[sid] if sid in mresult else ""] for sid, sname in sresult.items()}
for mid, mname in mresult.items():
    if mid in result:
        result[mid][1] = mname
    else:
        result[mid] = ["", mname]
result = list(map(lambda e: (e[0], e[1][0], e[1][1]), result.items()))
result.sort(key=lambda e: (int(e[0]), e[1], e[2]))
result = list(map(str, result))
print("\n".join(result))

from time import time

start = time()

for anime_id in range(1, 100):
    res = shikimori_api.client.get(f"https://shikimori.one/api/animes/{anime_id}")
    if res.status_code == 404:
        print(f'[t+{time()-start:.2f}] req {anime_id} result 404')
    else:
        r = res.json()
        print(f'[t+{time()-start:.2f}] req {anime_id} result {(r["id"], r["name"])}')

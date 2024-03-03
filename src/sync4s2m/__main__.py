from sync4s2m import logger
from sync4s2m.auth import ShikimoriAPIManager

import requests


shikimori_api = ShikimoriAPIManager()
shikimori_api.login()

id_ = shikimori_api.whoami["id"]
result = shikimori_api.client.get(f"https://shikimori.one/api/users/{id_}/anime_rates", params={"limit": 5000}).json()
result = [e["anime"]["russian"] for e in result]
print(result)

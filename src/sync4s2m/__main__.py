from sync4s2m import logger
from sync4s2m.auth import ShikimoriTokenSaver

import requests


shikimori_token_saver = ShikimoriTokenSaver()
shikimori_token_saver.load()

request = requests.get("https://shikimori.one/api/users/whoami", headers=shikimori_token_saver.headers())
if request.status_code == 200:
    logger.info(request.text)

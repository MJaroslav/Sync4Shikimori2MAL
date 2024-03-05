from sync4s2m.config import Config
from sync4s2m.auth import ShikimoriAPIManager, MyAnimeListAPIManager
from authlib.integrations.requests_client import OAuth2Session

import logging


class Sync4Shikimori2MAL(object):
    def __init__(self):
        self.logger = self._init_logger_()
        self.config = self._init_config_(self.logger)
        self.config.load()
        self.shikimori = self._init_shikimori_(self.logger, self.config)
        self.myanimelist = self._init_myanimelist_(self.logger, self.config)

    def _init_logger_(self) -> logging.Logger:
        result = logging.getLogger("")
        result.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        result.addHandler(handler)
        return result

    def _init_config_(self, logger: logging.Logger) -> Config:
        return Config(logger)

    def _init_shikimori_(
        self, logger: logging.Logger, config: Config
    ) -> ShikimoriAPIManager:
        return ShikimoriAPIManager(logger, config)

    def _init_myanimelist_(
        self, logger: logging.Logger, config: Config
    ) -> MyAnimeListAPIManager:
        return MyAnimeListAPIManager(logger, config)

    def login(self) -> tuple[OAuth2Session]:
        self.shikimori.login()
        self.myanimelist.login()
        return (self.shikimori, self.myanimelist)

    def get_shikimori_list(self) -> list:
        api = self.shikimori.client
        animes = []
        index = 1
        while True:
            page = api.get(
                f"/users/{self.shikimori.whoami['id']}/anime_rates",
                params={"limit": 5000, "page": index},
            ).json()
            animes += page
            if len(page) <= 5000:
                break
            index += 1
        mangas = []
        ranobes = []
        index = 1
        while True:
            page = api.get(
                f"/users/{self.shikimori.whoami['id']}/manga_rates",
                params={"limit": 5000, "page": index},
            ).json()
            for e in page:
                if "/ranobe/" in e["manga"]["url"]:
                    e["ranobe"] = e["manga"]
                    del e["manga"]
                    ranobes.append(e)
                else:
                    mangas.append(e)
            if len(page) <= 5000:
                break
            index += 1
        result = [("anime", anime) for anime in animes]
        result += [("manga", manga) for manga in mangas]
        result += [("ranobe", ranobe) for ranobe in ranobes]
        return result

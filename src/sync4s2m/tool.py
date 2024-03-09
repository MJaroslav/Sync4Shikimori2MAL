from sync4s2m.config import Config
from sync4s2m.auth import ShikimoriAPIManager, MyAnimeListAPIManager
from sync4s2m.titlelist import Title, TitleList, parse_shikimori, parse_myanimelist
from authlib.integrations.requests_client import OAuth2Session

import logging


class Sync4Shikimori2MAL(object):
    def __init__(self, args):
        self.logger = self._init_logger_()
        self.config = self._init_config_(self.logger, args)
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

    def _init_config_(self, logger: logging.Logger, args) -> Config:
        return Config(logger, args)

    def _init_shikimori_(
        self, logger: logging.Logger, config: Config
    ) -> ShikimoriAPIManager:
        return ShikimoriAPIManager(logger, config)

    def _init_myanimelist_(
        self, logger: logging.Logger, config: Config
    ) -> MyAnimeListAPIManager:
        return MyAnimeListAPIManager(logger, config)

    def login(self) -> tuple[OAuth2Session]:
        self.logger.info("Login and creating API sessions...")
        self.shikimori.login()
        self.myanimelist.login()
        self.logger.info("API sessions created and authorized")
        return (self.shikimori, self.myanimelist)

    def logout(self):
        self.logger.info("Shutting down API sessions...")
        self.shikimori.close()
        self.myanimelist.close()
        self.logger.info("API sessions closed")

    def get_shikimori_list(self) -> TitleList:
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
                    ranobes.append(e)
                else:
                    mangas.append(e)
            if len(page) <= 5000:
                break
            index += 1
        result = [
            Title("anime", raw_title=anime, parse_func=parse_shikimori)
            for anime in animes
        ]
        result += [
            Title("manga", raw_title=manga, parse_func=parse_shikimori)
            for manga in mangas
        ]
        result += [
            Title("ranobe", raw_title=ranobe, parse_func=parse_shikimori)
            for ranobe in ranobes
        ]
        return TitleList(result)

    def get_myanimelist_list(self) -> TitleList:
        api = self.myanimelist.client
        animes = []
        index = 0
        while True:
            page = api.get(
                f"/users/@me/animelist",
                params={
                    "limit": 1000,
                    "offset": index,
                    "fields": "list_status,media_type,status,alternative_titles",
                },
            ).json()
            animes += page["data"]
            if not "next" in page["paging"]:
                break
            index += 1000
        mangas = []
        index = 0
        while True:
            page = api.get(
                f"/users/@me/mangalist",
                params={
                    "limit": 1000,
                    "offset": index,
                    "fields": "list_status,media_type,status,alternative_titles",
                },
            ).json()
            mangas += page["data"]
            if not "next" in page["paging"]:
                break
            index += 1000
        result = [
            Title("anime", raw_title=anime, parse_func=parse_myanimelist)
            for anime in animes
        ]
        result += [
            Title("manga", raw_title=manga, parse_func=parse_myanimelist)
            for manga in mangas
        ]
        return TitleList(result)

    def get_delta(self, source: str = "shikimori") -> TitleList:
        shikimori = self.get_shikimori_list()
        myanimelist = self.get_myanimelist_list()

        if source == "shikimori":
            return shikimori.delta(myanimelist)
        elif source == "myanimelist":
            return myanimelist.delta(shikimori)
        else:
            raise NotImplementedError(f"Source {source} not implemented")

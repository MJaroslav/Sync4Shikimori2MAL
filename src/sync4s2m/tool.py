from sync4s2m.config import Config
from sync4s2m.auth import ShikimoriAPIManager, MyAnimeListAPIManager
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
                    ranobes.append(e)
                else:
                    mangas.append(e)
            if len(page) <= 5000:
                break
            index += 1
        result = [("anime", status, status["anime"]) for status in animes]
        result += [("manga", status, status["manga"]) for status in mangas]
        result += [("ranobe", status, status["manga"]) for status in ranobes]
        return result

    def get_myanimelist_list(self) -> list:
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
        animes = [("anime", e["list_status"], e["node"]) for e in animes]
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
        mangas = [("manga", e["list_status"], e["node"]) for e in mangas]
        return animes + mangas

    def get_delta(self, source: str = "shikimori"):
        shikimori = {e[2]["id"]: e for e in self.get_shikimori_list()}
        myanimelist = {e[2]["id"]: e for e in self.get_myanimelist_list()}

        if source == "shikimori":
            added = list(
                map(
                    lambda l: l[1],
                    filter(lambda e: not e[0] in myanimelist, shikimori.items()),
                )
            )
            for e in added:
                e[1]["delta"] = self.uni_status(e[1])
            removed = list(
                map(
                    lambda l: l[1],
                    filter(lambda e: not e[0] in shikimori, myanimelist.items()),
                )
            )
            for e in removed:
                e[1]["status"] = "deleted"
                e[1]["delta"] = {}
            shared = list(
                map(
                    lambda l: l[1],
                    filter(lambda e: e[0] in myanimelist, shikimori.items()),
                )
            )
            edited = []
            for e in shared:
                status_source = self.uni_status(e[1])
                status_target = self.uni_status(myanimelist[e[2]["id"]][1])
                if status_source != status_target:
                    e[1]["delta"] = dict(status_source.items() ^ status_target.items())
                    edited.append(e)
            return (
                [("added", e) for e in added]
                + [("edited", e) for e in edited]
                + [("deleted", e) for e in removed]
            )
        elif source == "myanimelist":
            added = list(
                map(
                    lambda l: l[1],
                    filter(lambda e: not e[0] in shikimori, myanimelist.items()),
                )
            )
            for e in added:
                e[1]["delta"] = self.uni_status(e[1])
            removed = list(
                map(
                    lambda l: l[1],
                    filter(lambda e: not e[0] in myanimelist, shikimori.items()),
                )
            )
            for e in removed:
                e[1]["status"] = "deleted"
                e[1]["delta"] = {}
            shared = list(
                map(
                    lambda l: l[1],
                    filter(lambda e: e[0] in shikimori, myanimelist.items()),
                )
            )
            edited = []
            for e in shared:
                status_source = self.uni_status(e[1])
                status_target = self.uni_status(shikimori[e[2]["id"]][1])
                if status_source != status_target:
                    e[1]["delta"] = dict(status_source.items() ^ status_target.items())
                    edited.append(e)
            return (
                [("added", e) for e in added]
                + [("edited", e) for e in edited]
                + [("deleted", e) for e in removed]
            )
        else:
            raise NotImplementedError(f"Source {source} not implemented")

    def uni_status(self, source: dict) -> str:
        status_data = {}

        # Use shikimori status enums as uni format + "deleted"
        status_data["list_status"] = source["status"]
        if (
            status_data["list_status"] == "plan_to_watch"
            or status_data["list_status"] == "plan_to_read"
        ):
            status_data["list_status"] = "planned"
        if status_data["list_status"] == "reading":
            status_data["list_status"] = "watching"
        if "is_rewatching" in source and source["is_rewatching"]:
            status_data["list_status"] = "rewatching"

        status_data["score"] = source["score"]

        if "episodes" in source:
            status_data["episodes"] = source["episodes"]
        elif "num_episodes_watched" in source:
            status_data["episodes"] = source["num_episodes_watched"]
        else:
            status_data["episodes"] = 0
        if status_data["episodes"] is None:
            status_data["episodes"] = 0

        if "chapters" in source:
            status_data["chapters"] = source["chapters"]
        elif "num_chapters_read" in source:
            status_data["chapters"] = source["num_chapters_read"]
        else:
            status_data["chapters"] = 0
        if status_data["chapters"] is None:
            status_data["chapters"] = 0

        status_data["count"] = max(status_data["episodes"], status_data["chapters"])

        if "volumes" in source:
            status_data["volumes"] = source["volumes"]
        elif "num_volumes_read" in source:
            status_data["volumes"] = source["num_volumes_read"]
        else:
            status_data["volumes"] = 0
        if status_data["volumes"] is None:
            status_data["volumes"] = 0

        if "rewatches" in source:
            status_data["rewatches"] = source["rewatches"]
        elif "num_times_rewatched" in source:
            status_data["rewatches"] = source["num_times_rewatched"]
        elif "num_times_reread" in source:
            status_data["rewatches"] = source["num_times_reread"]
        else:
            status_data["rewatches"] = 0

        if "text" in source:
            status_data["text"] = source["text"]
        elif "comments" in source:
            status_data["text"] = source["comments"]
        else:
            status_data["text"] = ''
        if status_data["text"] is None:
            status_data["text"] = ''
        
        if "delta" in source:
            status_data["delta"] = source["delta"]
        return status_data

    def uni_obj(self, source: list) -> list:
        obj = {}
        obj["id"] = source["id"]
        obj["name"] = source["name"] if "name" in source else source["title"]
        obj["type"] = source["kind"] if "kind" in source else source["media_type"]
        obj["name_ru"] = source["russian"] if "russian" in source and source["russian"] else obj["name"]
        obj["name_en"] = obj["name"]
        obj["name_ja"] = obj["name"]
        if "english" in source and source["english"]:
            obj["name_en"] = source["english"]
        if "japanese" in source and source["japanese"]:
            obj["name_ja"] = source["japanese"]
        if "alternative_titles" in source:
            alt = source["alternative_titles"]
            if "en" in alt:
                obj["name_en"] = alt["en"]
            if "ja" in alt:
                obj["name_ja"] = alt["ja"]
        obj["title_status"] = source["status"]
        if obj["title_status"] == "finished_airing" or obj["title_status"] == "finished":
            obj["title_status"] = "released"
        if obj["title_status"] == "currently_airing" or obj["title_status"] == "currently_publishing":
            obj["title_status"] = "ongoing"
        if obj["title_status"] == "not_yet_aired" or obj["title_status"] == "not_yet_published":
            obj["title_status"] = "anons"
        return obj

    def uni_list(self, source: list) -> list:
        if source and len(source[0]) == 2:  # Delta list
            return [(e[0], (e[1][0], self.uni_status(e[1][1]), self.uni_obj(e[1][2]))) for e in source]
        elif source and len(source[0]) == 3:  # Just list
            return [(e[0], self.uni_status(e[1]), self.uni_obj(e[2])) for e in source]
        else:
            raise ValueError(f"{source} is not supported list")
    
    def to_format_dict(self, source: list) -> dict:
        try:
            if source and len(source[0]) == 2:  # Delta list
                result = []
                for e in source:
                    formatted = dict(e[1][1])
                    formatted.update(e[1][2])
                    formatted["title_type"] = e[1][0]
                    formatted["modify_type"] = e[0]
                    result.append(formatted)
                return result
            elif source and len(source[0]) == 3:  # Just list
                result = []
                for e in source:
                    formatted = dict(e[1])
                    formatted.update(e[2])
                    formatted["title_type"] = e[0]
                    formatted["modify_type"] = "unmodified"
                    result.append(formatted)
                return result
            else:
                raise ValueError(f"{source} is not supported list")
        except KeyError:
            raise ValueError("f{source} is not unified list")

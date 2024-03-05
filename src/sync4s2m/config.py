from pathlib import Path
from pyrate_limiter import Duration, RequestRate, Limiter

import os
import json
import platformdirs


ENV_HOME_PATH = "SYNC4S2M_HOME"


class Config(object):
    def __init__(self, logger):
        self.logger = logger
        self.__values__ = {
            "shikimori": {
                "app_name": "",
                "client_id": "",
                "client_secret": "",
                "port": 0,
                "domain": "one",
            },
            "myanimelist": {"client_id": "", "port": 0},
            "rate_limiter": {
                "shikimori": [
                    {"count": 5, "unit": "SECOND", "factor": 1},
                    {"count": 90, "unit": "MINUTE", "factor": 1},
                ],
                "myanimelist": [
                    {"count": 5, "unit": "SECOND", "factor": 1},
                    {"count": 90, "unit": "MINUTE", "factor": 1},
                ],
            },
        }

    @staticmethod
    def get_config_dir(create: bool = False) -> Path:
        if ENV_HOME_PATH in os.environ:
            result = Path(os.environ[ENV_HOME_PATH])
            if create:
                result.mkdir(parents=True, exist_ok=True)
            return result
        return platformdirs.user_config_dir(
            appname="sync4s2m", appauthor="MJaroslav", ensure_exists=create
        )

    def __validate__(self) -> bool:
        result = False
        if not "shikimori" in self.__values__:
            self.__values__["shikimori"] = {}
        shiki = self.__values__["shikimori"]
        if not (
            shiki
            and "app_name" in shiki
            and shiki["app_name"]
            and "client_id" in shiki
            and shiki["client_id"]
            and "client_secret" in shiki
            and shiki["client_secret"]
            and "port" in shiki
            and shiki["port"] > 0
            and "domain" in shiki
            and shiki["domain"]
        ):
            self.logger.warn("Invalid Shikimori block, put actual values")
            shiki["app_name"] = input("App name: ")
            shiki["client_id"] = input("Client ID: ")
            shiki["client_secret"] = input("Client secret: ")
            shiki["port"] = int(input("Port: "))
            shiki["domain"] = input("Domain: ")
            result = True
        if not "myanimelist" in self.__values__:
            self.__values__["myanimelist"] = {}
        mal = self.__values__["myanimelist"]
        if not (
            mal
            and "client_id" in mal
            and mal["client_id"]
            and "port" in mal
            and mal["port"] > 0
        ):
            self.logger.warn("Invalid MyAnimeList block, put actual values")
            mal["client_id"] = input("Client ID: ")
            mal["port"] = int(input("Port: "))
            result = True
        if not "rate_limiter" in self.__values__:
            self.__values__["rate_limiter"] = {}
        limiter = self.__values__["rate_limiter"]
        if not "shikimori" in limiter or not limiter["shikimori"]:
            limiter["shikimori"] = [
                {"count": 5, "unit": "SECOND", "factor": 1},
                {"count": 90, "unit": "MINUTE", "factor": 1},
            ]
            result = True
        if not "myanimelist" in limiter or not limiter["myanimelist"]:
            limiter["myanimelist"] = [
                {"count": 5, "unit": "SECOND", "factor": 1},
                {"count": 90, "unit": "MINUTE", "factor": 1},
            ]
            result = True
        return result

    def get(self, key: str, do_raise=True) -> any:
        result = self.__values__
        for step in key.split("."):
            if step in result:
                result = result[step]
            elif do_raise:
                raise KeyError(f"Can't find '{step}' step in '{key}' key")
            else:
                return None
        return result

    def get_limiter(self, name: str) -> Limiter:
        params = self.get(f"rate_limiter.{name}")
        rates = [
            RequestRate(
                param["count"], getattr(Duration, param["unit"]) * param["factor"]
            )
            for param in params
        ]
        return Limiter(*rates)

    def load(self):
        self.logger.info("Configuration loading...")
        path = self.get_config_dir(True) / "config.json"
        if not path.is_file():
            self.logger.info("Configuration file not found, creating default...")
            with open(path, "w") as file:
                json.dump(self.__values__, file, indent=2)
        with open(path, "r") as file:
            self.__values__ = json.load(file)
        self.logger.info("Configuration validation...")
        if self.__validate__():
            with open(path, "w") as file:
                json.dump(self.__values__, file, indent=2)
        self.logger.info("Configuration loaded...")

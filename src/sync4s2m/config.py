from pathlib import Path

import os
import platform
import shutil
import json


ENV_HOME_PATH = "SYNC4S2M_HOME"
ENV_APPDATA = "APPDATA"
ENV_XDG_CONFIG = "XDG_CONFIG_HOME"


def get_config_dir(create: bool = False) -> Path:
    result = None
    if ENV_HOME_PATH in os.environ:
        result = Path(os.environ[ENV_HOME_PATH])
    elif platform.system() == "Linux":
        if ENV_XDG_CONFIG in os.environ:
            result = Path(os.environ[ENV_XDG_CONFIG])
        else:
            result = Path.home() / ".config" / "sync4s2m"
    elif platform.system() == "Windows":
        result = Path(os.environ[ENV_APPDATA]) / ".sync4s2m"
    else:
        raise NotImplementedError(f"Platform {patform.system} not implemented")
    if create:
        result.mkdir(parents=True, exist_ok=True)
    return result


class Config(object):
    def __init__(self, logger):
        self.logger = logger
        self.__values__ = {
            "shikimori": {"app_name": "", "client_id": "", "client_secret": "", "port": 0, "domain": "one"},
            "myanimelist": {"client_id": "", "port": 0}
        }

    def __validate__(self) -> bool:
        result = False
        if not "shikimori" in self.__values__:
            self.__values__["shikimori"] = {}
        shiki = self.__values__["shikimori"]
        if not (shiki and shiki["app_name"] and shiki["client_id"] and shiki["client_secret"] and shiki["port"] > 0 and shiki["domain"]):
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
        if not (mal and mal["client_id"] and mal["port"] > 0):
            self.logger.warn("Invalid MyAnimeList block, put actual values")
            mal["client_id"] = input("Client ID: ")
            mal["port"] = int(input("Port: "))
            result = True
        return True

    def get(self, key: str) -> any:
        result = self.__values__
        for step in key.split("."):
            result = result[step]
        return result

    def load(self):
        self.logger.info("Configuration loading...")
        path = get_config_dir(True) / "config.json"
        if not path.is_file():
            logger.info("Configuration file not found, creating default...")
            with open(path, "w") as file:
                json.dump(self.__values__, file, indent=2)
        with open(path, "r") as file:
            self.__values__ = json.load(file)
        self.logger.info("Configuration validation...")
        if self.__validate__():
            with open(path, "w") as file:
                json.dump(self.__values__, file, indent=2)
        self.logger.info("Configuration loaded...")

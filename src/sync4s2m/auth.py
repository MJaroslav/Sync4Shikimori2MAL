from fastapi import FastAPI, APIRouter, Response
from sync4s2m import logger, cfg
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime

import uvicorn
import os
import signal
import webbrowser
import requests
import json
import sync4s2m.config as config


class CodeServer(object):
    def __init__(self, handle_code_func, port: int):
        self.port = port
        self.handle_code_func = handle_code_func
        self.app = FastAPI()
        self.router = APIRouter()
        self.router.add_api_route("/", self.get_code, methods=["GET"])
        self.app.include_router(self.router)

    def get_code(self, code: str):
        self.handle_code_func(code)
        self.shutdown()
        return Response(status_code=200, content="Authorized")

    def start(self):
        logger.info("Starting code listener")
        uvicorn.run(self.app, host="localhost", port=self.port)

    def shutdown(self):
        os.kill(os.getpid(), signal.SIGTERM)
        logger.info("Code listener stopped")


class TokenSaver(object):
    def __init__(self, store_file: str, port: int):
        self.store_file = store_file
        self.port = port

    def _get_auth_code_url_(self) -> str:
        raise NotImplementedError()

    def _handle_code_(self, code: str):
        raise NotImplementedError()

    def _request_code_(self):
        url = self._get_auth_code_url_()
        logger.info(
            "Try open new browser tab for authorize. If this does not happen, follow the link manually:"
        )
        logger.info(url)
        webbrowser.open_new_tab(url)
        server = CodeServer(self._handle_code_, self.port)
        server.start()

    def validate_token(self) -> bool:
        raise NotImplementedError()

    def get_path(self) -> Path:
        return config.get_config_dir(True) / self.store_file

    def get_token(self) -> str:
        raise NotImplementedError()

    def refresh_token(self):
        raise NotImplementedError()

    def load(self):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def headers(self, headers: dict = None) -> dict:
        raise NotImplementedError()


class ShikimoriTokenSaver(TokenSaver):
    def __init__(self):
        super().__init__("shikimori.auth.json", cfg.get("shikimori.port"))
        self.app_name = cfg.get("shikimori.app_name")
        self.client_secret = cfg.get("shikimori.client_secret")
        self.client_id = cfg.get("shikimori.client_id")
        self.__token__ = {}

    def _get_auth_code_url_(self) -> str:
        return (
            "https://shikimori.one/oauth/authorize"
            + f"?client_id={self.client_id}"
            + f"&redirect_uri={quote_plus(f'http://localhost:{self.port}/')}"
            + "&response_type=code"
            + "&scope=user_rates"
        )

    def _handle_code_(self, code: str):
        logger.info("Authorized")
        headers = {"User-Agent": self.app_name}
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": f"http://localhost:{self.port}",
        }
        request = requests.post(
            "https://shikimori.one/oauth/token", params=params, headers=headers
        )
        if request.status_code == 200:
            self.__token__ = request.text
            self.save()

    def refresh_token(self):
        logger.info("Refreshing token...")
        headers = {
            "User-Agent": self.app_name,
        }
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.__token__["refresh_token"],
        }
        request = requests.post(
            "https://shikimori.one/oauth/token", params=params, headers=headers
        )
        if request.status_code == 200:
            self.__token__ = request.text
            self.save()

    def load(self):
        path = self.get_path()
        if not path.is_file():
            logger.info("Shikimori not authorized, login...")
            self.request_code()
        else:
            with open(path, "r") as file:
                self.__token__ = json.load(file)
            if not self.validate_token():
                self.refresh_token()

    def save(self):
        with open(self.get_path(), "w") as file:
            json.dump(self.__token__, file, indent=2)
        logger.info("Shikimori token saved")

    def validate_token(self) -> bool:
        if "created_at" in self.__token__ and "expires_in" in self.__token__:
            timestamp = self.__token__["created_at"] + self.__token__["expires_in"]
            return (
                datetime.now() - datetime.fromtimestamp(timestamp)
            ).total_seconds() < 0
        return False

    def get_token(self) -> str:
        if not self.validate_token():
            self.refresh_token()
        return self.__token__["access_token"]

    def headers(self, headers: dict = None) -> dict:
        headers = headers if headers else {}
        headers["User-Agent"] = self.app_name
        headers["Authorization"] = f'{self.__token__["token_type"]} {self.get_token()}'
        return headers

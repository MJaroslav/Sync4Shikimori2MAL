from sync4s2m import logger, cfg
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from authlib.integrations.requests_client import OAuth2Session
from authlib.common.security import generate_token

import webbrowser
import requests
import json
import sync4s2m.config as config


class OAuthHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            '<html><head><script type="application/javascript">window.close();</script><head><body>Authorized, you can close this page now.<body><html>'.encode(
                "UTF-8"
            )
        )
        self.server.result = self.path

    def log_message(self, format, *args):
        pass  # NO, GOD! PLEASE! NO!


class OAuthHTTPServer(HTTPServer):
    def __init__(self, port: int):
        super().__init__(("localhost", port), OAuthHTTPHandler)
        self.result = None


class OAuth2SessionWithUserAgent(OAuth2Session):
    def __init__(self, user_agent: str, *args, **kwargs):
        OAuth2Session.__init__(self, *args, **kwargs)
        self.user_agent = user_agent

    def request(self, method, url, withhold_token=False, auth=None, **kwargs):
        headers = {}
        if "headers" in kwargs:
            headers = kwargs["headers"]
            del kwargs["headers"]
        headers["User-Agent"] = self.user_agent
        return super().request(
            method,
            url,
            withhold_token=withhold_token,
            auth=auth,
            headers=headers,
            **kwargs,
        )


class APIManager(object):
    def __init__(
        self,
        name: str,
        auth_uri: str,
        token_uri: str,
        client_id: str,
        client_secret: str,
        port: int,
        scope: list[str],
        session_class=OAuth2Session,
        session_kwargs: dict = {},
    ):
        self.name = name
        self.auth_uri = auth_uri
        self.token_uri = token_uri
        self.client_id = client_id
        self.client_secret = client_secret
        self.port = port
        self.scope = scope
        self.__session_class__ = session_class
        self.__session_kwargs__ = session_kwargs
        self.__session__ = None
        self.whoami = None
        self.state = None
        self.use_pkce = (
            session_kwargs["code_challenge_method"]
            if "code_challenge_method" in session_kwargs
            else None
        )

    def _on_token_refresh_(self, token, **kwargs):
        logger.info(f"Token refreshed by {self.token_uri}")
        self.save_token()

    def load_token(self) -> dict:
        path = config.get_config_dir(True) / f"{self.name}.auth.json"
        if path.is_file():
            with open(path, "r") as file:
                return json.load(file)
        return {}

    def save_token(self):
        with open(config.get_config_dir(True) / f"{self.name}.auth.json", "w") as file:
            json.dump(self.client.token, file, indent=2)

    def login(self):
        if not self.client.token:
            with OAuthHTTPServer(self.port) as httpd:
                code_verifier = generate_token(128)
                extra_kwargs = {}
                if self.use_pkce:
                    if self.use_pkce == "plain":
                        extra_kwargs["code_challenge"] = code_verifier
                    else:
                        extra_kwargs["code_verifier"] = code_verifier
                    extra_kwargs["code_challenge_method"] = self.use_pkce
                uri, self.state = self.client.create_authorization_url(
                    self.auth_uri, **extra_kwargs
                )
                logger.info(
                    "Trying to open the authorization link in the browser, do it yourself otherwise:"
                )
                logger.info(uri)
                webbrowser.open_new(uri)
                httpd.handle_request()
                self.__session__ = None
                extra_kwargs = {}
                if self.use_pkce:
                    extra_kwargs["code_verifier"] = code_verifier
                self.client.fetch_token(
                    authorization_response=httpd.result, **extra_kwargs
                )
                self.save_token()
        self.whoami = self._whoami_()

    def refresh_token(self):
        self.client.refresh_token(self.token_uri)

    @property
    def client(self):
        if not self.__session__:
            token = self.load_token()
            self.__session__ = self.__session_class__(
                client_id=self.client_id,
                client_secret=self.client_secret,
                authorization_endpoint=self.auth_uri,
                token_endpoint=self.token_uri,
                scope=self.scope,
                token=token if token else None,
                redirect_uri=f"http://localhost:{self.port}/",
                update_token=self._on_token_refresh_,
                state=self.state,
                **self.__session_kwargs__,
            )
        return self.__session__

    def _whoami_(self):
        raise NotImplementedError()


class ShikimoriAPIManager(APIManager):
    def __init__(self):
        super().__init__(
            "shikimori",
            f"https://shikimori.{cfg.get('shikimori.domain')}/oauth/authorize",
            f"https://shikimori.{cfg.get('shikimori.domain')}/oauth/token",
            cfg.get("shikimori.client_id"),
            cfg.get("shikimori.client_secret"),
            cfg.get("shikimori.port"),
            ["user_rates"],
            OAuth2SessionWithUserAgent,
            {"user_agent": cfg.get("shikimori.app_name")},
        )

    def login(self):
        super().login()
        logger.info(f"Shikimori authorized as {self.whoami['nickname']}")

    def _whoami_(self):
        return self.client.get(
            f"https://shikimori.{cfg.get('shikimori.domain')}/api/users/whoami"
        ).json()


class MyAnimeListAPIManager(APIManager):
    def __init__(self):
        super().__init__(
            "myanimelist",
            f"https://myanimelist.net/v1/oauth2/authorize",
            f"https://myanimelist.net/v1/oauth2/token",
            cfg.get("myanimelist.client_id"),
            None,
            cfg.get("myanimelist.port"),
            ["write:users"],
            session_kwargs={"code_challenge_method": "plain"},
        )

    def login(self):
        super().login()
        logger.info(f"MyAnimeList authorized as {self.whoami['name']}")

    def _whoami_(self):
        return self.client.get("https://api.myanimelist.net/v2/users/@me").json()

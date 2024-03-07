from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from authlib.integrations.requests_client import OAuth2Session
from authlib.common.security import generate_token
from requests_ratelimiter import LimiterAdapter
from logging import Logger
from sync4s2m.config import Config


import webbrowser
import requests
import json


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


class OAuth2SessionWithURLPrefix(OAuth2Session):
    def __init__(self, prefix: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = prefix

    def request(self, method, url, withhold_token=False, auth=None, **kwargs):
        if url.startswith("/"):
            url = f"{self.prefix}{url}"
        return super().request(
            method,
            url,
            withhold_token=withhold_token,
            auth=auth,
            **kwargs,
        )


class OAuth2SessionWithUserAgent(OAuth2SessionWithURLPrefix):
    def __init__(self, prefix: str, user_agent: str, *args, **kwargs):
        super().__init__(prefix=prefix, *args, **kwargs)
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
        logger: Logger,
        config: Config,
        name: str,
        auth_uri: str,
        token_uri: str,
        scope: list[str],
        prefix_url: str,
        session_class=OAuth2SessionWithURLPrefix,
        session_kwargs: dict = {},
    ):
        self.logger = logger
        self.config = config
        self.name = name
        self.auth_uri = auth_uri
        self.token_uri = token_uri
        self.client_id = self.config.get(f"{name}.client_id")
        self.client_secret = self.config.get(f"{name}.client_secret", False)
        self.port = self.config.get(f"{name}.port")
        self.scope = scope
        self.prefix_url = prefix_url
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
        self.logger.info(f"Token of {self.name} refreshed")
        self.save_token()

    def load_token(self) -> dict:
        path = self.config.get_config_dir(True) / f"{self.name}.auth.json"
        if path.is_file():
            with open(path, "r") as file:
                return json.load(file)
        return {}

    def save_token(self):
        with open(
            self.config.get_config_dir(True) / f"{self.name}.auth.json", "w"
        ) as file:
            json.dump(self.client.token, file, indent=2)
            self.logger.info(f"Saved token for {self.name} rewritten")

    def login(self):
        if not self.client.token:
            self.logger.info(f"No saved token for {self.name} found, try to login...")
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
                self.logger.info(
                    "Trying to open the authorization link in the browser, do it yourself otherwise:"
                )
                self.logger.info(uri)
                webbrowser.open_new(uri)
                httpd.handle_request()
                self.logger.info(f"Recreating session for {self.name}...")
                self.__session__ = None
                extra_kwargs = {}
                if self.use_pkce:
                    extra_kwargs["code_verifier"] = code_verifier
                self.client.fetch_token(
                    authorization_response=httpd.result, **extra_kwargs
                )
                self.save_token()
        else:
            self.logger.info(f"Found saved token for {self.name}")
        self.whoami = self._whoami_()

    def refresh_token(self):
        self.logger.info(f"Force token update for {self.name}")
        self.client.refresh_token(self.token_uri)

    @property
    def client(self):
        if not self.__session__:
            self.logger.info(f"Creating session for {self.name}...")
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
                prefix=self.prefix_url,
                **self.__session_kwargs__,
            )
            adapter = LimiterAdapter(limiter=self.config.get_limiter(self.name))
            self.__session__.mount("https://", adapter)
            self.__session__.mount("http://", adapter)
        return self.__session__

    def _whoami_(self):
        raise NotImplementedError()


class ShikimoriAPIManager(APIManager):
    def __init__(self, logger: Logger, config: Config):
        super().__init__(
            logger,
            config,
            "shikimori",
            f"https://shikimori.{config.get('shikimori.domain')}/oauth/authorize",
            f"https://shikimori.{config.get('shikimori.domain')}/oauth/token",
            ["user_rates"],
            f"https://shikimori.{config.get('shikimori.domain')}/api",
            OAuth2SessionWithUserAgent,
            {"user_agent": config.get("shikimori.app_name")},
        )

    def login(self):
        super().login()
        self.logger.info(f"Shikimori authorized as {self.whoami['nickname']}")

    def _whoami_(self):
        return self.client.get("/users/whoami").json()


class MyAnimeListAPIManager(APIManager):
    def __init__(self, logger: Logger, config: Config):
        super().__init__(
            logger,
            config,
            "myanimelist",
            f"https://myanimelist.net/v1/oauth2/authorize",
            f"https://myanimelist.net/v1/oauth2/token",
            ["write:users"],
            "https://api.myanimelist.net/v2",
            session_kwargs={"code_challenge_method": "plain"},
        )

    def login(self):
        super().login()
        self.logger.info(f"MyAnimeList authorized as {self.whoami['name']}")

    def _whoami_(self):
        return self.client.get("/users/@me").json()

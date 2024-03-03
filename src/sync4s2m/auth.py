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
            '<script type="application/javascript">window.close();</script>'.encode(
                "UTF-8"
            )
        )
        self.server.result = self.path


class OAuthHTTPServer(HTTPServer):
    def __init__(self, port: int):
        HTTPServer.__init__(self, ("localhost", port), OAuthHTTPHandler)
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
        token_file: str,
        auth_uri: str,
        token_uri: str,
        client_id: str,
        client_secret: str,
        port: int,
        scope: list[str],
        session_class=OAuth2Session,
        session_kwargs: dict = {},
    ):
        self.token_file = token_file
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

    def _on_token_refresh_(self, token, **kwargs):
        logger.info(f"Token refreshed by {self.token_uri}")
        self.save_token()

    def load_token(self) -> dict:
        path = config.get_config_dir(True) / self.token_file
        if path.is_file():
            with open(path, "r") as file:
                return json.load(file)
        return {}

    def save_token(self):
        with open(config.get_config_dir(True) / self.token_file, "w") as file:
            json.dump(self.client.token, file, indent=2)

    def login(self):
        if not self.client.token:
            with OAuthHTTPServer(self.port) as httpd:
                uri, state = client.create_authorization_url(self.auth_uri)
                logger.info("Trying to open the authorization link in the browser, do it yourself otherwise:")
                logger.info(uri)
                webbrowser.open_new_tab(uri)
                httpd.handle_request()
                client.fetch_token(authorization_response=httpd.result)
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
                **self.__session_kwargs__,
            )
        return self.__session__

    def _whoami_(self):
        raise NotImplementedError()

class ShikimoriAPIManager(APIManager):
    def __init__(self):
        super().__init__(
            "shikimori.token.json",
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
        return self.client.get(f"https://shikimori.{cfg.get('shikimori.domain')}/api/users/whoami").json()

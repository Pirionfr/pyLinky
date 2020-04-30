from typing import Optional, Union, Callable, Dict

from requests import Response
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from urllib.parse import urlencode


AUTHORIZE_URL_SANDBOX           = "https://gw.hml.api.enedis.fr/dataconnect/v1/oauth2/authorize"
ENDPOINT_TOKEN_URL_SANDBOX      = "https://gw.hml.api.enedis.fr/v1/oauth2/token"
METERING_DATA_BASE_URL_SANDBOX  = "https://gw.hml.api.enedis.fr"

AUTHORIZE_URL_PROD              = "https://gw.prd.api.enedis.fr/dataconnect/v1/oauth2/authorize"
ENDPOINT_TOKEN_URL_PROD         = "https://gw.prd.api.enedis.fr/v1/oauth2/token"
METERING_DATA_BASE_URL_PROD     = "https://gw.prd.api.enedis.fr"

class AbstractAuth:
    def __init__(
        self,
        token: Optional[Dict[str, str]] = None,
        client_id: str = None,
        client_secret: str = None,
        redirect_url: str = None,
        token_updater: Optional[Callable[[str], None]] = None,
        sandbox: bool = True
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_url = redirect_url
        self.token_updater = token_updater
        self.sandbox = sandbox

        extra = {"client_id": self.client_id, "client_secret": self.client_secret}

        self._oauth = OAuth2Session(
            auto_refresh_kwargs=extra,
            client_id=client_id,
            token=token,
            token_updater=token_updater,
        )

    def authorization_url(self, duration=""):
        url = AUTHORIZE_URL_PROD
        if (self.sandbox):
            url = AUTHORIZE_URL_SANDBOX
        return self._oauth.authorization_url(url, duration=duration)

    def refresh_tokens(self) -> Dict[str, Union[str, int]]:
        """Refresh and return new tokens."""
        print("Refresh token")
        url = ENDPOINT_TOKEN_URL_PROD
        if (self.sandbox):
            url = ENDPOINT_TOKEN_URL_SANDBOX
        if self.redirect_url is not None:
            url = url + "?" + urlencode({'redirect_uri': self.redirect_url})
        token = self._oauth.refresh_token(url, include_client_id=True, client_id=self.client_id, client_secret=self.client_secret, refresh_token=self._oauth.token)

        if self.token_updater is not None:
            self.token_updater(token)

        return token

    def request_token(self, code) -> Dict[str, Union[str, int]]:
        """return new tokens."""
        print("Fetch new token")
        url = ENDPOINT_TOKEN_URL_PROD
        if (self.sandbox):
            url = ENDPOINT_TOKEN_URL_SANDBOX
        print(self.redirect_url)
        if self.redirect_url is not None:
            url = url + "?" + urlencode({'redirect_uri': self.redirect_url})
        token = self._oauth.fetch_token(url, include_client_id=True, client_id=self.client_id, client_secret=self.client_secret, code=code)

        if self.token_updater is not None:
            self.token_updater(token)
        print(self.redirect_url)
        return token

    def request(self, path: str, arguments: Dict[str, str]) -> Response:
        """Make a request.
        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        print("request")
        url = METERING_DATA_BASE_URL_PROD
        if (self.sandbox):
            url = METERING_DATA_BASE_URL_SANDBOX
        url = url + path

        try:
            response = self._oauth.request("GET", url, params=arguments)
            if (response.status_code == 403):
                self._oauth.token = self.refresh_tokens()
            else:
                return response
        except TokenExpiredError:
            self._oauth.token = self.refresh_tokens()

            return self._oauth.request("GET", url, params=arguments)

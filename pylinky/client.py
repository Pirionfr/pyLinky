#    pyLink: Get your consumption data from your Enedis account
#    Copyright (C) 2018  Pirionfr, https://github.com/Pirionfr
#    Copyright (C) 2018  Ludovic Rousseau, <ludovic.rousseau@free.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import base64
import datetime
from dateutil.relativedelta import relativedelta
import requests


LOGIN_URL = "https://espace-client-connexion.enedis.fr/auth/UI/Login"
HOST = "https://espace-client-particuliers.enedis.fr/group/espace-particuliers"
DATA_URL = "{}/suivi-de-consommation".format(HOST)

REQ_PART = "lincspartdisplaycdc_WAR_lincspartcdcportlet"


class PyLinkyError(Exception):
    pass


class LinkyClient(object):
    def __init__(self, username, password, session=None, timeout=None):
        """Initialize the client object."""
        self.username = username
        self.password = password
        self._session = session
        self._data = {}
        self._timeout = timeout

    def _get_httpsession(self):
        """Set http session."""
        if self._session is None:
            self._session = requests.Session()
            self._post_login_page()

    def _post_login_page(self):
        """Login to enedis."""
        data = {
            "IDToken1": self.username,
            "IDToken2": self.password,
            "SunQueryParamsString": base64.b64encode(b"realm=particuliers"),
            "encoded": "true",
            "gx_charset": "UTF-8",
        }

        try:
            self._session.post(
                LOGIN_URL, data=data, allow_redirects=False, timeout=self._timeout
            )

        except OSError:
            raise PyLinkyError("Can not submit login form")

        if "iPlanetDirectoryPro" not in self._session.cookies:
            raise PyLinkyError("Login error: Please check your username/password.")

        return True

    def _get_data(self, p_p_resource_id, start_date=None, end_date=None):
        """Get data."""

        if start_date is not None:
            start_date = start_date.strftime("%d/%m/%Y")

        if end_date is not None:
            end_date = end_date.strftime("%d/%m/%Y")

        data = {
            "_" + REQ_PART + "_dateDebut": start_date,
            "_" + REQ_PART + "_dateFin": end_date,
        }

        params = {
            "p_p_id": REQ_PART,
            "p_p_lifecycle": 2,
            "p_p_state": "normal",
            "p_p_mode": "view",
            "p_p_resource_id": p_p_resource_id,
            "p_p_cacheability": "cacheLevelPage",
            "p_p_col_id": "column-1",
            "p_p_col_pos": 1,
            "p_p_col_count": 3,
        }

        try:
            raw_res = self._session.post(
                DATA_URL,
                data=data,
                params=params,
                allow_redirects=False,
                timeout=self._timeout,
            )

            if 300 <= raw_res.status_code < 400:
                raw_res = self._session.post(
                    DATA_URL,
                    data=data,
                    params=params,
                    allow_redirects=False,
                    timeout=self._timeout,
                )
        except OSError:
            raise PyLinkyError("Can not get data")

        if raw_res.status_code == 200 and raw_res.text is not None:
            if "Conditions d'utilisation" in raw_res.text:
                raise PyLinkyError(
                    "You need to accept the latest Terms of Use. Please manually log into the website, then come back."
                )
            if "Une erreur technique" in raw_res.text:
                raise PyLinkyError(
                    "A technical error has occurred on website. Data unavailable."
                )

        if raw_res.text is "":
            raise PyLinkyError("No data")

        try:
            json_output = raw_res.json()
        except (OSError, json.decoder.JSONDecodeError):
            raise PyLinkyError("Could not get data")

        if json_output.get("etat").get("valeur") == "erreur":
            raise PyLinkyError("Could not get data")

        return json_output.get("graphe")

    def get_data_per_hour(self, start_date, end_date):
        """Retreives hourly energy consumption data."""
        data = self._get_data("urlCdcHeure", start_date, end_date)
        data["time_format"] = "%H:%M"
        data["data_format"] = "hours"
        return data

    def get_data_per_day(self, start_date, end_date):
        """Retreives daily energy consumption data."""
        data = self._get_data("urlCdcJour", start_date, end_date)
        data["time_format"] = "%d %b"
        data["data_format"] = "days"
        return data

    def get_data_per_month(self, start_date, end_date):
        """Retreives monthly energy consumption data."""
        data = self._get_data("urlCdcMois", start_date, end_date)
        data["time_format"] = "%b"
        data["data_format"] = "months"
        return data

    def get_data_per_year(self):
        """Retreives yearly energy consumption data."""
        data = self._get_data("urlCdcAn")
        data["time_format"] = "%Y"
        data["data_format"] = "years"
        return data

    def format_data(self, data, time_format=None):
        result = []

        # Prevent from non existing data yet
        if not data:
            return []

        # Extract start date and parse it
        start_date = datetime.datetime.strptime(
            data.get("periode").get("dateDebut"), "%d/%m/%Y"
        ).date()

        if time_format is None:
            time_format = data["time_format"]
        format_data = data["data_format"]

        # Calculate final start date using the "offset" attribute returned by the API
        inc = 1
        if format_data == "hours":
            inc = 0.5

        kwargs = {format_data: data.get("decalage") * inc}
        start_date = start_date - relativedelta(**kwargs)

        # Generate data
        for ordre, value in enumerate(data.get("data")):
            kwargs = {format_data: ordre * inc}
            result.append(
                {
                    "time": (
                        (start_date + relativedelta(**kwargs)).strftime(time_format)
                    ),
                    "conso": (value.get("valeur") if value.get("valeur") > 0 else 0),
                }
            )

        return result

    def fetch_data(self):
        """Get the latest data from Enedis."""
        # Get http session
        self._get_httpsession()

        today = datetime.date.today()
        # last 2 days
        self._data["raw_hourly"] = self.get_data_per_hour(
            (today - relativedelta(days=1)), today
        )

        # last 30 days
        self._data["raw_daily"] = self.get_data_per_day(
            (today - relativedelta(days=30)), (today - relativedelta(days=1))
        )

        # 12 last month
        self._data["raw_monthly"] = self.get_data_per_month(
            (today - relativedelta(months=12)), (today - relativedelta(days=1))
        )

        # 12 last month
        self._data["raw_yearly"] = self.get_data_per_year()

    def login(self):
        # Get http session
        self._get_httpsession()

    def get_data(self):
        data = {}
        for data_kind in ("hourly", "daily", "monthly", "yearly"):
            data[data_kind] = self.format_data(self._data["raw_" + data_kind])

        return data

    def close_session(self):
        """Close current session."""
        self._session.close()
        self._session = None

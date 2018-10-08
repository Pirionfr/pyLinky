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
            'IDToken1': self.username,
            'IDToken2': self.password,
            'SunQueryParamsString': base64.b64encode(b'realm=particuliers'),
            'encoded': 'true',
            'gx_charset': 'UTF-8'
        }

        try:
            self._session.post(LOGIN_URL,
                                data=data,
                                allow_redirects=False,
                                timeout= self._timeout)

        except OSError:
            raise PyLinkyError("Can not submit login form")

        if 'iPlanetDirectoryPro' not in self._session.cookies:
            raise PyLinkyError("Login error: Please check your username/password.")

        return True

    def _get_data(self, p_p_resource_id, start_date=None, end_date=None):
        """Get data."""

        data = {
            '_' + REQ_PART + '_dateDebut': start_date,
            '_' + REQ_PART + '_dateFin': end_date
        }

        params = {
            'p_p_id': REQ_PART,
            'p_p_lifecycle': 2,
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_resource_id': p_p_resource_id,
            'p_p_cacheability': 'cacheLevelPage',
            'p_p_col_id': 'column-1',
            'p_p_col_pos': 1,
            'p_p_col_count': 3
        }

        try:
            raw_res = self._session.post(DATA_URL,
                                         data=data,
                                         params=params,
                                         allow_redirects=False,
                                         timeout=self._timeout)

            if 300 <= raw_res.status_code < 400:
                raw_res = self._session.post(DATA_URL,
                                             data=data,
                                             params=params,
                                             allow_redirects=False,
                                             timeout=self._timeout)
        except OSError:
            raise PyLinkyError("Can not get data")
        try:
            json_output = raw_res.json()
        except (OSError, json.decoder.JSONDecodeError):
            raise PyLinkyError("Could not get data")

        if  json_output.get('etat').get('valeur') == 'erreur':
            raise PyLinkyError("Could not get data")

        return json_output.get('graphe')

    def _get_data_per_hour(self, start_date, end_date):
        """Retreives hourly energy consumption data."""
        return self._format_data(self._get_data('urlCdcHeure', start_date, end_date), 'hours', "%H:%M")

    def _get_data_per_day(self, start_date, end_date):
        """Retreives daily energy consumption data."""
        return self._format_data(self._get_data('urlCdcJour', start_date, end_date), 'days', "%d %b")

    def _get_data_per_month(self, start_date, end_date):
        """Retreives monthly energy consumption data."""
        return self._format_data(self._get_data('urlCdcMois', start_date, end_date), 'months', "%b")

    def _get_data_per_year(self):
        """Retreives yearly energy consumption data."""
        return self._format_data(self._get_data('urlCdcAn'), 'years', "%Y")

    def _format_data(self, data, format_data, time_format):
        result = []

        # Prevent from non existing data yet
        if not data:
            return []

        # Extract start date and parse it
        start_date = datetime.datetime.strptime(data.get("periode").get("dateDebut"), "%d/%m/%Y").date()

        # Calculate final start date using the "offset" attribute returned by the API
        inc = 1
        if format_data == 'hours':
            inc = 0.5

        kwargs = {format_data: data.get('decalage') * inc}
        start_date = start_date - relativedelta(**kwargs)

        # Generate data
        for ordre, value in enumerate(data.get('data')):
            kwargs = {format_data: ordre * inc}
            result.append({"time": ((start_date + relativedelta(**kwargs)).strftime(time_format)),
                           "conso": (value.get('valeur') if value.get('valeur') > 0 else 0)})

        return result

    def fetch_data(self):
        """Get the latest data from Enedis."""
        # Get http session
        self._get_httpsession()

        today = datetime.date.today()
        # last 2 days
        self._data["hourly"] = self._get_data_per_hour((today - relativedelta(days=1)).strftime("%d/%m/%Y"),
                                                     today.strftime("%d/%m/%Y"))

        # last 30 days
        self._data["daily"] = self._get_data_per_day((today - relativedelta(days=30)).strftime("%d/%m/%Y"),
                                                       (today - relativedelta(days=1)).strftime("%d/%m/%Y"))

        # 12 last month
        self._data["monthly"] = self._get_data_per_month((today - relativedelta(months=12)).strftime("%d/%m/%Y"),
                                                         (today - relativedelta(days=1)).strftime("%d/%m/%Y"))

        # 12 last month
        self._data["yearly"] = self._get_data_per_year()

    def get_data(self):
        return self._data

    def close_session(self):
        """Close current session."""
        self._session.close()
        self._session = None

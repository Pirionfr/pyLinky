import json
import simplejson
import base64
import datetime
from dateutil.relativedelta import relativedelta
import requests
from fake_useragent import UserAgent


LOGIN_URL = "https://espace-client-connexion.enedis.fr/auth/UI/Login"
HOST = "https://espace-client-particuliers.enedis.fr/group/espace-particuliers"
DATA_URL = "{}/suivi-de-consommation".format(HOST)

REQ_PART = "lincspartdisplaycdc_WAR_lincspartcdcportlet"

HOURLY = "hourly"
DAILY = "daily"
MONTHLY = "monthly"
YEARLY = "yearly"


_DELTA = 'delta'
_FORMAT = 'format'
_RESSOURCE = 'ressource'
_DURATION = 'duration'
_MAP = {
    _DELTA: {HOURLY: 'hours', DAILY: 'days', MONTHLY: 'months', YEARLY: 'years'},
    _FORMAT: {HOURLY: "%H:%M", DAILY: "%d %b", MONTHLY: "%b", YEARLY: "%Y"},
    _RESSOURCE: {HOURLY: 'urlCdcHeure', DAILY: 'urlCdcJour', MONTHLY: 'urlCdcMois', YEARLY: 'urlCdcAn'},
    _DURATION: {HOURLY: 24, DAILY: 30, MONTHLY: 12, YEARLY: None}
}


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

    def login(self):
        """Set http session."""
        if self._session is None:
            self._session = requests.session()
            # adding fake user-agent header
            self._session.headers.update({'User-agent': str(UserAgent().random)})
        return self._post_login_page()

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
                               timeout=self._timeout)
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
        except OSError as e:
            raise PyLinkyError("Could not access enedis.fr: " + str(e))

        if raw_res.text is "":
            raise PyLinkyError("No data")

        if 302 == raw_res.status_code and "/messages/maintenance.html" in raw_res.text:
            raise PyLinkyError("Site in maintenance")

        try:
            json_output = raw_res.json()
        except (OSError, json.decoder.JSONDecodeError, simplejson.errors.JSONDecodeError) as e:
            raise PyLinkyError("Impossible to decode response: " + str(e) + "\nResponse was: " + str(raw_res.text))

        if json_output.get('etat').get('valeur') == 'erreur':
            raise PyLinkyError("Enedis.fr answered with an error: " + str(json_output))

        return json_output.get('graphe')

    def format_data(self, data, time_format=None):
        result = []

        # Prevent from non existing data yet
        if not data or not data.get("data"):
            return []

        period_type = data['period_type']
        if time_format is None:
            time_format = _MAP[_FORMAT][period_type]
        format_data = _MAP[_DELTA][period_type]

        # Extract start date and parse it
        if 'periode' in data:
            periode = data.get("periode")
            if not periode:
                return []
            start_date = datetime.datetime.strptime(periode.get("dateDebut"), "%d/%m/%Y").date()

        # Calculate final start date using the "offset" attribute returned by the API
        inc = 1
        if format_data == 'hours':
            inc = 0.5

        kwargs = {format_data: data.get('decalage') * inc}
        start_date = start_date - relativedelta(**kwargs)

        # Generate data
        for order, value in enumerate(data.get('data')):
            kwargs = {format_data: order * inc}
            result.append({"time": ((start_date + relativedelta(**kwargs)).strftime(time_format)),
                           "conso": (value.get('valeur') if value.get('valeur') > 0 else 0)})

        return result

    def get_data_per_period(self, period_type=HOURLY, start=None, end=None):
        today = datetime.date.today()
        if start is None:
            kwargs = {_MAP[_DELTA][period_type]: _MAP[_DURATION][period_type]}
            if period_type == YEARLY:
                start = None
            # 12 last complete months + current month
            elif period_type == MONTHLY:
                start = (today.replace(day=1) - relativedelta(**kwargs))
            else:
                start = (today - relativedelta(**kwargs))
        if end is None:
            if period_type == YEARLY:
                end = None
            elif period_type == HOURLY:
                end = today
            else:
                end = (today - relativedelta(days=1))

        if start is not None:
            start = start.strftime("%d/%m/%Y")
        if end is not None:
            end = end.strftime("%d/%m/%Y")

        data = self._get_data(_MAP[_RESSOURCE][period_type], start, end)
        data['period_type'] = period_type

        return data

    def fetch_data(self):
        """Get the latest data from Enedis."""

        for t in [HOURLY, DAILY, MONTHLY, YEARLY]:
            self._data[t] = self.get_data_per_period(t)

    def get_data(self):
        formatted_data = dict()
        for t in [HOURLY, DAILY, MONTHLY, YEARLY]:
            formatted_data[t] = self.format_data(self._data[t])
        return formatted_data

    def close_session(self):
        """Close current session."""
        self._session.close()
        self._session = None

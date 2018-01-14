import json
import base64
import datetime
from dateutil.relativedelta import relativedelta
import requests



LOGIN_URL = "https://espace-client-connexion.enedis.fr/auth/UI/Login"
HOST = "https://espace-client-particuliers.enedis.fr/group/espace-particuliers"
HOME_URL = '{}/accueil'.format(HOST)
DATA_URL = "{}/suivi-de-consommation".format(HOST)

REQ_PART = "lincspartdisplaycdc_WAR_lincspartcdcportlet"


class PyLinkyError(Exception):
    pass


class LinkyClient(object):
    def __init__(self, username, password, session=None):
        """Initialize the client object."""
        self.username = username
        self.password = password
        self._session = session
        self._data = {}

    def _get_httpsession(self):
        """Set http session."""
        if self._session is None:
            self._session = requests.Session()


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
            row_res = self._session.post(LOGIN_URL,
                                          data=data,
                                          allow_redirects=False);

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
                                         allow_redirects=False)

            if 300 <= raw_res.status_code < 400:
                raw_res = self._session.post(DATA_URL,
                                             data=data,
                                             params=params,
                                             allow_redirects=False)
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
        return self._get_data('urlCdcHeure', start_date, end_date)

    def _get_data_per_day(self, start_date, end_date):
        """Retreives daily energy consumption data."""
        return self._get_data( 'urlCdcJour', start_date, end_date)

    def _get_data_per_month(self, start_date, end_date):
        """Retreives monthly energy consumption data."""
        return self._get_data('urlCdcMois', start_date, end_date)

    def _get_data_per_year(self):
        """Retreives yearly energy consumption data."""
        return self._get_data('urlCdcAn')


    def fetch_data(self):
        """Get the latest data from Enedis."""
        # Get http session
        self._get_httpsession()
        # Post login page
        self._post_login_page()

        #last 30 days
        today = datetime.date.today()
        daily_data = self._get_data_per_day((today - relativedelta(days=30)).strftime("%d/%m/%Y"),
                                                       (today - relativedelta(days=1)).strftime("%d/%m/%Y"))


        self._data["daily"] = daily_data


    def get_data(self, contract=None):
        return self._data

    def close_session(self):
        """Close current session."""
        self._session.close()
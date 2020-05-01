import base64
import datetime
import json

import requests
import simplejson
from dateutil.relativedelta import relativedelta

from .exceptions import (PyLinkyAccessException, PyLinkyEnedisException,
                         PyLinkyException, PyLinkyMaintenanceException,
                         PyLinkyWrongLoginException)

from .abstractauth import AbstractAuth

SCOPE = {
"ADDRESSES": "/v3/customers/usage_points/addresses",
"CONSUMPTION_LOAD_CURVE": "/v4/metering_data/consumption_load_curve",
"CONTRACTS": "/v3/customers/usage_points/contracts",
"CONTACT_DATA": "/v3/customers/contact_data",
"DAILY_CONSUMPTION": "/v4/metering_data/daily_consumption",
"DAILY_CONSUMPTION_MAX_POWER": "/v4/metering_data/daily_consumption_max_power",
"IDENTITY": "/v3/customers/identity"
}

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

class LinkyClient(object):

    PERIOD_DAILY = DAILY
    PERIOD_MONTHLY = MONTHLY
    PERIOD_YEARLY = YEARLY
    PERIOD_HOURLY = HOURLY

    def __init__(self, auth: AbstractAuth, authorize_duration="P1Y", ):
        """Initialize the client object."""
        self.authorize_duration = authorize_duration
        self._auth = auth

    def get_authorisation_url(self, test_customer=""):
        auth_url = self._auth.authorization_url(self.authorize_duration, test_customer=test_customer)
        return auth_url[0]

    def request_tokens(self, code):
        self._auth.request_tokens(code)

    def get_consumption_load_curve(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request("/v4/metering_data/consumption_load_curve", argument_dictionnary)

    def get_production_load_curve(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request("/v4/metering_data/production_load_curve", argument_dictionnary)

    def get_daily_consumption_max_power(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request("/v4/metering_data/daily_consumption_max_power", argument_dictionnary)

    def get_daily_consumption(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request("/v4/metering_data/daily_consumption", argument_dictionnary)

    def get_daily_production(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request("/v4/metering_data/daily_production", argument_dictionnary)

    def get_customer_identity(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request("/v3/customers/identity", argument_dictionnary)

    def get_customer_contact_data(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request("/v3/customers/contact_data", argument_dictionnary)

    def get_customer_usage_points_contracts(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request("/v3/customers/usage_points/contracts", argument_dictionnary)

    def get_customer_usage_points_addresses(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request("/v3/customers/usage_points/addresses", argument_dictionnary)





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
            raise PyLinkyAccessException("Could not access enedis.fr: " + str(e))

        if raw_res.text is "":
            raise PyLinkyException("No data")

        if 302 == raw_res.status_code and "/messages/maintenance.html" in raw_res.text:
            raise PyLinkyMaintenanceException("Site in maintenance")

        try:
            json_output = raw_res.json()
        except (OSError, json.decoder.JSONDecodeError, simplejson.errors.JSONDecodeError) as e:
            raise PyLinkyException("Impossible to decode response: " + str(e) + "\nResponse was: " + str(raw_res.text))

        if json_output.get('etat').get('valeur') == 'erreur':
            raise PyLinkyEnedisException("Enedis.fr answered with an error: " + str(json_output))

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

        self._data[period_type] = data
        return data

    def fetch_data(self):
        """Get the latest data from Enedis."""
        for t in [HOURLY, DAILY, MONTHLY, YEARLY]:
            self.get_data_per_period(t)

    def get_data(self):
        formatted_data = dict()
        for t in [HOURLY, DAILY, MONTHLY, YEARLY]:
            if t in self._data:
                formatted_data[t] = self.format_data(self._data[t])
        return formatted_data

    def close_session(self):
        """Close current session."""
        self._auth.close()

import datetime
import json

import requests
import simplejson
from dateutil.relativedelta import relativedelta

from .exceptions import (PyLinkyAccessException, PyLinkyEnedisException,
                         PyLinkyException, PyLinkyMaintenanceException,
                         PyLinkyWrongLoginException)

from .abstractauth import AbstractAuth
from .linkyapi import LinkyAPI

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
    _DURATION: {HOURLY: 24, DAILY: 30, MONTHLY: 12, YEARLY: 3}
}

class LinkyClient(object):

    PERIOD_DAILY = DAILY
    PERIOD_MONTHLY = MONTHLY
    PERIOD_YEARLY = YEARLY
    PERIOD_HOURLY = HOURLY

    def __init__(self, auth: AbstractAuth, authorize_duration="P1Y"):
        """Initialize the client object."""
        self._api = LinkyAPI(auth, authorize_duration)
        self._data = {}

    def _get_data(self, p_p_resource_id, start_date=None, end_date=None):
        """Get data."""

        try:
            upids = self._api.get_usage_point_ids()
            if not upids:
                raise PyLinkyException("No usage point")
            upid = upids[0]
            if p_p_resource_id == 'urlCdcHeure':
                raw_res = self._api.get_consumption_load_curve(upids, start_date, end_date)
            else:
                raw_res = self._api.get_daily_consumption(upids, start_date, end_date)
        except OSError as e:
            raise PyLinkyAccessException("Could not access enedis.fr: " + str(e))

        if 404 == raw_res.status_code:
            raise PyLinkyException("No data")

        if 500 == raw_res.status_code:
            raise PyLinkyMaintenanceException("Site in maintenance")

        try:
            json_output = raw_res.json()
        except (OSError, json.decoder.JSONDecodeError, simplejson.errors.JSONDecodeError) as e:
            raise PyLinkyException("Impossible to decode response: " + str(e) + "\nResponse was: " + str(raw_res.text))

        if json_output.get('error'):
            description = json_output.get('error_description')
            description = json_output['error'] if description is None else description
            raise PyLinkyEnedisException("Enedis.fr answered with an error: " + description)

        return json_output['meter_reading']

    def format_data(self, data, time_format=None):
        result = []

        # Prevent from non existing data yet
        if not data:
            return []

        period_type = data['period_type']
        if time_format is None:
            time_format = _MAP[_FORMAT][period_type]
        format_data = _MAP[_DELTA][period_type]

        in_format_date = "%Y-%m-%d"
        if format_data == 'hours':
            in_format_date = "%Y-%m-%d %H:%M:%S"

        dicResult = dict()
        for p in data['interval_reading']:
            key = datetime.datetime.strptime(p['date'], in_format_date).strftime(time_format)
            dicResult[key] = dicResult.get(key, 0) + int(p['value'])

        # Generate data
        for key in dicResult:
            result.append({"time": key,
                           "conso": dicResult[key]})

        return result

    def get_data_per_period(self, period_type=HOURLY, start=None, end=None):
        today = datetime.date.today()
        if start is None:
            kwargs = {_MAP[_DELTA][period_type]: _MAP[_DURATION][period_type]}
            if period_type == YEARLY:
                start = (today - relativedelta(**kwargs))
            # 12 last complete months + current month
            elif period_type == MONTHLY:
                start = (today.replace(day=1) - relativedelta(**kwargs))
            else:
                start = (today - relativedelta(**kwargs))
        if end is None:
            if period_type == YEARLY:
                end = today
            elif period_type == HOURLY:
                end = today
            else:
                end = (today - relativedelta(days=1))

        if start is not None:
            start = start.strftime("%Y-%m-%d")
        if end is not None:
            end = end.strftime("%Y-%m-%d")

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
        self._api.close_session()

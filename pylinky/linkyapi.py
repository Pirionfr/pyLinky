from .abstractauth import AbstractAuth

SCOPE = {
"CONSUMPTION_LOAD_CURVE": "/v4/metering_data/consumption_load_curve",
"PRODUCTION_LOAD_CURVE": "/v4/metering_data/production_load_curve",
"DAILY_CONSUMPTION_MAX_POWER": "/v4/metering_data/daily_consumption_max_power",
"DAILY_PRODUCTION": "/v4/metering_data/daily_production",
"DAILY_CONSUMPTION": "/v4/metering_data/daily_consumption",
"IDENTITY": "/v3/customers/identity",
"CONTACT_DATA": "/v3/customers/contact_data",
"CONTRACTS": "/v3/customers/usage_points/contracts",
"ADDRESSES": "/v3/customers/usage_points/addresses"
}

class LinkyAPI(object):

    def __init__(self, auth: AbstractAuth, authorize_duration="P1Y", ):
        """Initialize the client object."""
        self.authorize_duration = authorize_duration
        self._auth = auth

    def get_authorisation_url(self, test_customer=""):
        auth_url = self._auth.authorization_url(self.authorize_duration, test_customer=test_customer)
        return auth_url[0]

    def request_tokens(self, code):
        self._auth.request_tokens(code)

    def get_usage_point_ids(self):
        return self._auth.get_usage_point_ids()

    def get_consumption_load_curve(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request(SCOPE['CONSUMPTION_LOAD_CURVE'], argument_dictionnary)

    def get_production_load_curve(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request(SCOPE['PRODUCTION_LOAD_CURVE'], argument_dictionnary)

    def get_daily_consumption_max_power(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request(SCOPE['DAILY_CONSUMPTION_MAX_POWER'], argument_dictionnary)

    def get_daily_consumption(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request(SCOPE['DAILY_CONSUMPTION'], argument_dictionnary)

    def get_daily_production(self, usage_point_id, start, end):
        argument_dictionnary = {'usage_point_id':usage_point_id, 'start': start, 'end': end}
        return self._auth.request(SCOPE['DAILY_PRODUCTION'], argument_dictionnary)

    def get_customer_identity(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request(SCOPE['IDENTITY'], argument_dictionnary)

    def get_customer_contact_data(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request(SCOPE['CONTACT_DATA'], argument_dictionnary)

    def get_customer_usage_points_contracts(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request(SCOPE['CONTRACTS'], argument_dictionnary)

    def get_customer_usage_points_addresses(self, usage_point_id):
        argument_dictionnary = {'usage_point_id': usage_point_id}
        return self._auth.request(SCOPE['ADDRESSES'], argument_dictionnary)

    def close_session(self):
        """Close current session."""
        self._auth.close()

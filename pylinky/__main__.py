import argparse
import sys
import json
from urllib.parse import urlparse, parse_qs

from pylinky import LinkyClient, AbstractAuth

import logging
import contextlib
from http.client import HTTPConnection

def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--client-id',
                        required=True, help='Client ID from Enedis')
    parser.add_argument('-s', '--client-secret',
                        required=True, help='Client Secret from Enedis')
    parser.add_argument('-u', '--redirect-url',
                        required=True, help='Redirect URL as stated in the Enedis admin console')
    args = parser.parse_args()


    '''Switches on logging of the requests module.'''
    HTTPConnection.debuglevel = 2
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    '''Switches on logging of the requests module.'''

    auth = AbstractAuth(client_id=args.client_id, client_secret=args.client_secret, redirect_url=args.redirect_url)
    client = LinkyClient(auth)

    try:
        authorization_url = client.get_authorisation_url()
        print("Please go to {} and authorize access.".format(authorization_url))
        authorization_response = input("Enter the full callback URL")
        authorization_response_qa = parse_qs(urlparse(authorization_response).query)

        code = authorization_response_qa["code"][0]
        usage_point_id = authorization_response_qa["usage_point_id"][0]
        state = authorization_response_qa["state"][0]

        token = client.request_tokens(code)
        print(token)
        # Not needed, just a test to make sure that refresh_tokens works
        auth.refresh_tokens()
        print(token)

        response = client.get_consumption_load_curve(usage_point_id, "2020-03-01", "2020-03-05")
        print(response.content)
        input("Press a key")

        response = client.get_production_load_curve(usage_point_id, "2020-03-01", "2020-03-05")
        print(response.content)
        input("Press a key")

        response = client.get_daily_consumption_max_power(usage_point_id, "2020-03-01", "2020-03-05")
        print(response.content)
        input("Press a key")

        response = client.get_daily_consumption(usage_point_id, "2020-03-01", "2020-03-05")
        print(response.content)
        input("Press a key")

        response = client.get_daily_production(usage_point_id, "2020-03-01", "2020-03-05")
        print(response.content)
        input("Press a key to exit")
    except BaseException as exp:
        print(exp)
        return 1
    finally:
        client.close_session()


if __name__ == '__main__':
    sys.exit(main())


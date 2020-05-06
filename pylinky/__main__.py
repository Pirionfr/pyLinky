import argparse
import sys
import json
from urllib.parse import urlparse, parse_qs

from pylinky import LinkyAPI, AbstractAuth, LinkyClient

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
    parser.add_argument('-t', '--test-consumer',
                        required=False, help='Test consumer for sandbox 0-9')
    parser.add_argument('-v', '--verbose',
                        required=False, action='store_true', help='Verbose, debug network calls')
    args = parser.parse_args()

    if (args.verbose):
        '''Switches on logging of the requests module.'''
        HTTPConnection.debuglevel = 2
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    test_consumer = args.test_consumer

    auth = AbstractAuth(client_id=args.client_id, client_secret=args.client_secret, redirect_url=args.redirect_url)
    linky_api = LinkyAPI(auth)

    try:
        authorization_url = linky_api.get_authorisation_url(test_customer=test_consumer)
        print("Please go to \n{}\nand authorize access.".format(authorization_url))
        authorization_response = input("Enter the full callback URL :\n")
        authorization_response_qa = parse_qs(urlparse(authorization_response).query)

        code = authorization_response_qa["code"][0]
        state = authorization_response_qa["state"][0]

        token = linky_api.request_tokens(code)
        # Not needed, just a test to make sure that refresh_tokens works
        token = auth.refresh_tokens()

        usage_point_ids = linky_api.get_usage_point_ids()


        for usage_point_id in usage_point_ids:
            print(usage_point_id)

            response = linky_api.get_customer_identity(usage_point_id)
            print("get_customer_identity")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_customer_contact_data(usage_point_id)
            print("get_customer_contact_data")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_customer_usage_points_contracts(usage_point_id)
            print("get_customer_usage_points_contracts")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_customer_usage_points_addresses(usage_point_id)
            print("get_customer_usage_points_addresses")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_consumption_load_curve(usage_point_id, "2020-03-01", "2020-03-05")
            print("get_consumption_load_curve")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_production_load_curve(usage_point_id, "2020-03-01", "2020-03-05")
            print("get_production_load_curve")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_daily_consumption_max_power(usage_point_id, "2020-03-01", "2020-03-05")
            print("get_daily_consumption_max_power")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_daily_consumption(usage_point_id, "2020-03-01", "2020-03-05")
            print("get_daily_consumption")
            print(response.content)
            #input("Press a key")

            response = linky_api.get_daily_production(usage_point_id, "2020-03-01", "2020-03-05")
            print("get_daily_production")
            print(response.content)
            #input("Press a key")

        linky_client = LinkyClient(auth)
        linky_client.fetch_data()
        data = linky_client.get_data()
        print(data)


    except BaseException as exp:
        print(exp)
        return 1
    finally:
        linky_api.close_session()
        linky_client.close_session()


if __name__ == '__main__':
    sys.exit(main())


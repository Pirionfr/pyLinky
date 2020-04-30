import argparse
import sys
import json
from urllib.parse import urlparse, parse_qs

from pylinky import LinkyClient

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


    client = LinkyClient(args.client_id, args.client_secret, args.redirect_url)

    try:
        authorization_url = client.get_authorisation_url()
        print("Please go to {} and authorize access.".format(authorization_url))
        authorization_response = input("Enter the full callback URL")
        authorization_response_qa = parse_qs(urlparse(authorization_response).query)

        code = authorization_response_qa["code"][0]
        usage_point_id = authorization_response_qa["usage_point_id"][0]
        state = authorization_response_qa["state"][0]

        token = client.request_token(code)

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
        print ("finally")
        #client.close_session()
    #print(json.dumps(client.get_data(), indent=2))
    print ("the end")


if __name__ == '__main__':
    sys.exit(main())


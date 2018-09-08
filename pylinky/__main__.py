import argparse
import sys
import json

from pylinky import LinkyClient

def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        required=True, help='enedis username')
    parser.add_argument('-p', '--password',
                        required=True, help='Password')
    args = parser.parse_args()

    client = LinkyClient(args.username, args.password)


    try:
        client.fetch_data()
    except BaseException as exp:
        print(exp)
        return 1
    finally:
        client.close_session()
    print(json.dumps(client.get_data(), indent=2))


if __name__ == '__main__':
    sys.exit(main())


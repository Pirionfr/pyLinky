#!/usr/bin/env python

#    pylink: get your consumption data from your enedis account
#    copyright (c) 2018  pirionfr, https://github.com/pirionfr
#    copyright (c) 2018  ludovic rousseau, <ludovic.rousseau@free.fr>
#
#    this program is free software: you can redistribute it and/or modify
#    it under the terms of the gnu general public license as published by
#    the free software foundation, either version 3 of the license, or
#    (at your option) any later version.
#
#    this program is distributed in the hope that it will be useful,
#    but without any warranty; without even the implied warranty of
#    merchantability or fitness for a particular purpose.  see the
#    gnu general public license for more details.
#
#    you should have received a copy of the gnu general public license
#    along with this program.  if not, see <https://www.gnu.org/licenses/>.

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


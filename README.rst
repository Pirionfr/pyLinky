
pyLinky
=======

.. image:: https://travis-ci.org/Pirionfr/pyLinky.svg?branch=master
    :target: https://travis-ci.org/Pirionfr/pyLinky

.. image:: https://img.shields.io/pypi/v/pyLinky.svg
    :target: https://pypi.python.org/pypi/pyLinky

.. image:: https://img.shields.io/pypi/pyversions/pyLinky.svg
    :target: https://pypi.python.org/pypi/pyLinky

.. image:: https://requires.io/github/Pirionfr/pyLinky/requirements.svg?branch=master
    :target: https://requires.io/github/Pirionfr/pyLinky/requirements/?branch=master
    :alt: Requirements Status

Get your consumption data from your Enedis account (www.enedis.fr)

In order to use the library, you need an account on https://datahub-enedis.fr/.
You need to create a Data Connect Application and as of May 2020 you will get
your client_id by mail and your client_secret by SMS after a week or so...
With these credentials, you can only access the Sandbox environment... You need
to sign a contract and probably wait more to get Production credentials...

The library uses requests and requests_oauthlib to cope with the OAuth 2.0
protocol. It uses an AbstractAuth class to let a developer override the refresh
token function and route it via their own external service.
It also let the storage of the token between sessions to the developer.



Installation
------------

The easiest way to install the library is using `pip <https://pip.pypa.io/en/stable/>`_::

    pip install pylinky

You can also download the source code and install it manually::

    cd /path/to/pylinky/
    python setup.py install

Usage
-----
Print your current data

    pylinky -c <client_id> -s <client_secret> -u <redirect_url>

Dev env
-------
create virtual env and install requirements

    virtualenv -p /usr/bin/python3.5 env
    pip install -r requirements.txt


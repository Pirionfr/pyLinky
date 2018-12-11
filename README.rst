
pyLinky
=======

.. image:: https://travis-ci.org/LudovicRousseau/pyLinky.svg?branch=master
    :target: https://travis-ci.org/LudovicRousseau/pyLinky

Get your consumption data from your Enedis account (www.enedis.fr) 

This library This is based on jeedom_linky, created by Outadoc (https://github.com/Asdepique777/jeedom_linky)

Installation
------------

Download the source code and install it manually::

    cd /path/to/pylinky/
    python setup.py install

This pyLinky module is a fork of https://github.com/Pirionfr/pyLinky. The version available on pypi https://pypi.org/project/pylinky/ is the old/original version. I hope the two versions will merge someday. See https://github.com/Pirionfr/pyLinky/issues/9.

Usage
-----
Print your current data

    pylinky -u <USERNAME> -p <PASSWORD>

Dev env
-------
create virtual env and install requirements

    virtualenv -p /usr/bin/python3.5 env
    pip install -r requirements.txt


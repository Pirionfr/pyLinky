
pyLinky
=======
Get your consumption data from your Enedis account (www.enedis.fr) 

This library This is based on jeedom_linky, created by Outadoc (https://github.com/Asdepique777/jeedom_linky)

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

    pylink -u <USERNAME> -p <PASWORD>

Dev env
-------
create virtual env and install requirements

    virtualenv -p /usr/bin/python3.5 env
    pip install -r requirements.txt

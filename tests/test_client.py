import unittest
import requests_mock
import responses

# Our test case class
import requests
from pylinky import LinkyClient
from pylinky.client import LOGIN_URL


class LinkyClientTestCase(unittest.TestCase):

    def test_LinkyClient(self):
        username = "test_login"
        password = "test_password"
        client = LinkyClient(username, password)
        assert client.username == username
        assert client.password == password
        assert client._timeout is None

    def test_LinkyClientWithTimeout(self):
        username = "test_login"
        password = "test_password"

        client = LinkyClient(username, password, timeout=1)
        assert client.username == username
        assert client.password == password
        assert client._timeout == 1

    def test_LinkyClientWithSession(self):
        username = "test_login"
        password = "test_password"
        session = requests.session()

        client = LinkyClient(username, password, session=session)
        assert client.username == username
        assert client.password == password
        assert client._session == session

    @requests_mock.Mocker()
    def test_login(self, m):
        cookies = {'iPlanetDirectoryPro': 'test'}

        m.register_uri('POST', LOGIN_URL, status_code=200, cookies=cookies)
        client = LinkyClient("test_login", "test_password")

        client.login()

    def test(self):
        data = None
        if not data:
            assert True
        else:
            assert False


if __name__ == "__main__":
    unittest.main()
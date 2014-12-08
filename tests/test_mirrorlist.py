import os
import imp
import mock
import unittest
import webtest
import subprocess

mirrorlist_client = imp.load_source('mirrorlist_client',
        os.path.join('..', 'mirrorlist', 'mirrorlist_client.wsgi'))


class TestMirrorlistClient(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp(mirrorlist_client.application)
        mirrorlist_client.get_mirrorlist = mock.MagicMock(name='get_mirrorlist')
        mirrorlist_client.get_mirrorlist.return_value = {
            'resulttype': 'mirrorlist',
            'message': u'# repo = updates-testing-f20 arch = x86_64 country = global ',
            'returncode': 200,
            'results': [
                (293, u'http://ftp.jaist.ac.jp/pub/Linux/Fedora/updates/testing/20/x86_64/'),
                (475, u'http://ftp.iij.ad.jp/pub/linux/fedora/updates/testing/20/x86_64/'),
                (501, u'http://ftp.riken.jp/Linux/fedora/updates/testing/20/x86_64/'),
                (1747, u'https://ftp.fau.de/fedora/linux/updates/testing/20/x86_64/'),
            ],
        }

    def tearDown(self):
        pass

    def test_mirrorlist(self):
        resp = self.app.get('/mirrorlist', {
            'repo': 'updates-testing-f20', 'arch': 'x86_64',
        }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)
        mirrorlist_client.get_mirrorlist.assert_called_once_with({
            'repo': u'updates-testing-f20',
            'client_ip': u'127.0.0.1',
            'metalink': False,
            'arch': u'x86_64'
        })
        self.assertEquals(resp.body, """# repo = updates-testing-f20 arch = x86_64 country = global 
http://ftp.jaist.ac.jp/pub/Linux/Fedora/updates/testing/20/x86_64/
http://ftp.iij.ad.jp/pub/linux/fedora/updates/testing/20/x86_64/
http://ftp.riken.jp/Linux/fedora/updates/testing/20/x86_64/
https://ftp.fau.de/fedora/linux/updates/testing/20/x86_64/
""")


if __name__ == '__main__':
    unittest.main()

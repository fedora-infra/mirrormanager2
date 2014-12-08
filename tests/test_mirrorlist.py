import os
import imp
import mock
import unittest
import webtest
import subprocess

mirrorlist_client = imp.load_source('mirrorlist_client',
        os.path.join('..', 'mirrorlist', 'mirrorlist_client.wsgi'))

mirrorlist_server_result = {
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

metalink_result = {'resulttype': 'metalink', 'message': None, 'returncode': 200, 'results': u'<?xml version="1.0" encoding="utf-8"?>\n<metalink version="3.0" xmlns="http://www.metalinker.org/" type="dynamic" pubdate="Mon, 08 Dec 2014 22:57:10 GMT" generator="mirrormanager" xmlns:mm0="http://fedorahosted.org/mirrormanager">\n  <files>\n    <file name="repomd.xml">\n      <mm0:timestamp>1417039796</mm0:timestamp>\n      <size>4988</size>\n      <verification>\n        <hash type="md5">83abbe55aa0d5ef3b73759a4424b89e4</hash>\n        <hash type="sha1">86cc1a187310fc2b2be511d65226f3fe1993933a</hash>\n        <hash type="sha256">14f3c79d942f376974b5ef0660b981d1fb1ed362cff16e2b1e5e6714cabd089b</hash>\n        <hash type="sha512">1b190360a98346f2bb7f6ddec81b23b768ee5171dfb8af8c64ee961072be8c0fbe7098309bb5785f8d4b4138822cb645b0b0aa203a378612a82912b826459a08</hash>\n      </verification>\n      <resources maxconnections="1">\n        <url protocol="rsync" type="rsync" location="CA" preference="100" >rsync://mirror.nexicom.net/Fedora/updates/testing/20/x86_64/repodata/repomd.xml</url>\n        <url protocol="http" type="http" location="CA" preference="100" >http://fedora.mirror.nexicom.net/linux/updates/testing/20/x86_64/repodata/repomd.xml</url>\n        <url protocol="rsync" type="rsync" location="NL" preference="99" >rsync://mirror.1000mbps.com/fedora/linux/updates/testing/20/x86_64/repodata/repomd.xml</url>\n      </resources>\n    </file>\n  </files>\n</metalink>\n'}

mirrorlist_result = """# repo = updates-testing-f20 arch = x86_64 country = global 
http://ftp.jaist.ac.jp/pub/Linux/Fedora/updates/testing/20/x86_64/
http://ftp.iij.ad.jp/pub/linux/fedora/updates/testing/20/x86_64/
http://ftp.riken.jp/Linux/fedora/updates/testing/20/x86_64/
https://ftp.fau.de/fedora/linux/updates/testing/20/x86_64/
"""


class TestMirrorlistClient(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp(mirrorlist_client.application)
        mirrorlist_client.get_mirrorlist = mock.MagicMock(name='get_mirrorlist')

    def tearDown(self):
        pass

    def test_mirrorlist(self):
        mirrorlist_client.get_mirrorlist.return_value = mirrorlist_server_result
        resp = self.app.get('/mirrorlist', {
            'repo': 'updates-testing-f20', 'arch': 'x86_64',
        }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)
        mirrorlist_client.get_mirrorlist.assert_called_once_with({
            'repo': u'updates-testing-f20',
            'client_ip': u'127.0.0.1',
            'metalink': False,
            'arch': u'x86_64'
        })
        self.assertEquals(resp.body, mirrorlist_result)

    def test_metalink(self):
        mirrorlist_client.get_mirrorlist.return_value = metalink_result
        resp = self.app.get('/metalink', {
            'repo': 'updates-testing-f20', 'arch': 'x86_64',
        }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=200)
        mirrorlist_client.get_mirrorlist.assert_called_once_with({
            'repo': u'updates-testing-f20',
            'client_ip': u'127.0.0.1',
            'metalink': True,
            'arch': u'x86_64'
        })
        self.assertEquals(resp.body, metalink_result['results'])
        proc = subprocess.Popen(['xmllint', '--noout', '-'],
                                stdin=subprocess.PIPE)
        proc.stdin.write(resp.body)
        out, err = proc.communicate()
        assert proc.returncode == 0, proc.returncode

    def test_mirrorlist_redirect(self):
        mirrorlist_client.get_mirrorlist.return_value = mirrorlist_server_result
        resp = self.app.get('/mirrorlist', {
            'repo': 'updates-testing-f20',
            'arch': 'x86_64',
            'redirect': '1'
        }, extra_environ={'REMOTE_ADDR': '127.0.0.1'}, status=302)
        self.assertEquals(resp.headers['Location'],
                          mirrorlist_server_result['results'][0][1])


if __name__ == '__main__':
    unittest.main()

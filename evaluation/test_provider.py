"""Offline deployment-adapter tests; no real credentials or network access."""
import json
import os
import unittest
from unittest.mock import MagicMock, patch
import provider_config as config
import search_serper as adapter


class ProviderTests(unittest.TestCase):
    def fake(self, payload):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return opener

    @patch.dict(os.environ, {'SERPER_API_KEY': 'test-only-value'}, clear=True)
    def test_schema_and_request(self):
        opener = self.fake({'organic': [{'link': 'https://example.org/', 'title': 'Source', 'snippet': 'Text'},
                                       {'link': 'https://example.net/'}]})
        with patch.object(adapter.urllib.request, 'build_opener', return_value=opener):
            rows = adapter.search('a query', 1, 10)
        self.assertEqual(rows, [{'url': 'https://example.org/', 'title': 'Source', 'snippet': 'Text'}])
        req = opener.open.call_args.args[0]
        self.assertEqual(req.full_url, adapter.ENDPOINT)
        self.assertEqual(req.get_method(), 'POST')
        self.assertEqual(json.loads(req.data), {'q': 'a query', 'num': 1})
        self.assertEqual(req.get_header('X-api-key'), 'test-only-value')

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_no_request(self):
        with patch.object(adapter.urllib.request, 'build_opener') as network:
            with self.assertRaisesRegex(RuntimeError, 'SERPER_API_KEY'):
                adapter.search('query', 1, 10)
            network.assert_not_called()

    @patch.dict(os.environ, {'SERPER_API_KEY': 'test-only-value'}, clear=True)
    def test_errors_do_not_echo_credentials(self):
        opener = MagicMock()
        opener.open.side_effect = ValueError('test-only-value echoed by upstream')
        with patch.object(adapter.urllib.request, 'build_opener', return_value=opener):
            with self.assertRaises(RuntimeError) as caught:
                adapter.search('query', 1, 10)
        self.assertNotIn('test-only-value', str(caught.exception))

    @patch.dict(os.environ, {'SERPER_API_KEY': 'test-only-value'}, clear=True)
    def test_malformed_results(self):
        opener = self.fake({'organic': [None, {'link': 'file:///example'}, {'link': 'https://user:pass@example.org'},
                                       {'link': 'https://example.org/'}]})
        with patch.object(adapter.urllib.request, 'build_opener', return_value=opener):
            self.assertEqual(adapter.search('query', 10, 10), [{'url': 'https://example.org/', 'title': '', 'snippet': ''}])

    def test_no_redirect(self):
        self.assertIsNone(adapter.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.net/'))

    def test_endpoint_rejects_embedded_credentials(self):
        for value in ('http://example.org/', 'https://u:p@example.org/', 'https://example.org/?key=example'):
            with patch.dict(os.environ, {'COMPAREDR_JUDGE_ENDPOINT': value}):
                with self.assertRaises(ValueError):
                    config.endpoint('COMPAREDR_JUDGE_ENDPOINT')

    @patch.dict(os.environ, {'SERPER_API_KEY': 'test-only-value'}, clear=True)
    def test_limits(self):
        with patch.object(adapter.urllib.request, 'build_opener') as network:
            for k in (0, 101, True):
                with self.assertRaises(ValueError):
                    adapter.search('query', k, 10)
            with self.assertRaises(ValueError):
                adapter.search('', 1, 10)
            network.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""Optional Serper search transport; credentials and raw errors are never logged."""
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ENDPOINT = 'https://google.serper.dev/search'
MAX_RESPONSE_BYTES = 2_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the provider credential to a redirect target.
        return None


def search(query, top_k, timeout):
    key = os.environ.get('SERPER_API_KEY', '').strip()
    if not key:
        raise RuntimeError('Configure SERPER_API_KEY outside the repository')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Search query must be nonempty')
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        raise ValueError('top_k must be between 1 and 100')
    if not 0 < timeout <= 300:
        raise ValueError('timeout must be between 0 and 300 seconds')
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps({'q': query, 'num': top_k}).encode('utf-8'),
        headers={'X-API-KEY': key, 'Content-Type': 'application/json'}, method='POST')
    try:
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError('Response exceeds size limit')
        payload = json.loads(raw)
        rows = payload['organic']
        if not isinstance(rows, list):
            raise ValueError('Expected organic results')
        result = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            link = row.get('link', '')
            if not isinstance(link, str):
                continue
            url = urlsplit(link)
            if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
                continue
            result.append({'url': link, 'title': str(row.get('title', '')),
                           'snippet': str(row.get('snippet', ''))})
            if len(result) == top_k:
                break
        return result
    except Exception as exc:
        # Provider responses may echo request headers. Preserve only the class.
        raise RuntimeError('Serper request failed (' + type(exc).__name__ + ')') from None

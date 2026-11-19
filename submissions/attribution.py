"""Build offline notices from the pinned release records, not a second license database."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
QUERY_NOTICES = (
    'LICENSE', 'licenses/DRB-I-LICENSE.txt', 'licenses/DRB-II-DATA-LICENSE.txt',
    'licenses/CC-BY-4.0.txt', 'licenses/ResearchRubrics-MIT-LICENSE.txt',
    'licenses/QUERY_LICENSE_MATRIX.md', 'licenses/DRB2_ARTICLE_ATTRIBUTIONS.md',
)


def query_notices():
    paths = (*QUERY_NOTICES, 'submissions/QUERY_ATTRIBUTION.md')
    return {Path(path).name if path.startswith('submissions/') else path:
            (REPO / path).read_bytes() for path in paths}


def site_notices():
    files = {name: (REPO / name).read_bytes() for name in ('LICENSE', 'NOTICE', 'DATA_LICENSE.md')}
    files.update({'licenses/' + path.name: path.read_bytes()
                  for path in sorted((REPO / 'licenses').iterdir()) if path.is_file() and not path.name.startswith('.')})
    vendor = 'website/longcat-blog/vendor/LONGCAT_MIT_LICENSE.txt'
    files['licenses/LONGCAT_MIT_LICENSE.txt'] = (REPO / vendor).read_bytes()
    files['THIRD_PARTY_NOTICES.md'] = (REPO / 'THIRD_PARTY_NOTICES.md').read_text().replace(
        '(' + vendor + ')', '(licenses/LONGCAT_MIT_LICENSE.txt)').encode()
    return files


def standalone_credits(queries):
    # Also embed the texts, not just paths into a site that might not accompany the JSON.
    wanted = {(q['id'], q[key]['id']) for q in queries for key in ('pt_example', 'pw_example')}
    rows = [r for r in json.loads((REPO / 'licenses/CRITERION_LICENSE_MAP.json').read_text())
            if (r['query_id'], r['criterion_id']) in wanted]
    if len(rows) != len(wanted) or {(r['query_id'],r['criterion_id']) for r in rows} != wanted:
        raise ValueError('Missing or duplicate provenance for displayed criterion examples')
    return dict(scope='Keep these credits with redistributed queries and criterion examples. '
                      'Upstream licenses remain applicable; CC BY 4.0 covers only eligible CompareDR contributions.',
                project='CompareDR', repository='https://github.com/CompareDR/CompareDR',
                notices={name: content.decode() for name, content in query_notices().items()},
                criterion_provenance=rows)

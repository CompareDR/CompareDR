"""Build a deterministic, query-only intake template. No reports or keys included."""
import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def build():
    queries = []
    for path in sorted((REPO / 'data/evaluation/main9/rubrics').glob('*.json')):
        item = json.loads(path.read_text(encoding='utf-8'))
        queries.append(dict(query_id=path.stem, language=item['language'], query=item['full_query']))
    if len(queries) != 40:
        raise ValueError('Expected exactly 40 original queries')
    reference = dict(benchmark='CompareDR', query_set='comparedr-40', queries=queries)
    from validate import QUERYSET_SHA256
    if hashlib.sha256(encode(reference)).hexdigest() != QUERYSET_SHA256:
        raise ValueError('Frozen query set changed; review and version the intake contract before rebuilding')
    (HERE / 'queries.json').write_bytes(encode(reference))
    manifest = dict(schema_version='1.0', benchmark='CompareDR', query_set='comparedr-40',
        system=dict(name='', model='', harness='', reasoning='', generation_start='', generation_end='', settings={}),
        permission_to_evaluate=False, redistribution_notes='',
        reports=[dict(query_id=q['query_id'],status='completed',report_path='reports/'+q['query_id']+'.md',sha256='',notes='') for q in queries])
    (HERE / 'submission.template.json').write_bytes(encode(manifest))
    readme = (HERE / 'README.md').read_text(encoding='utf-8')
    # In the downloaded package, the ZIP link must not point to a missing repo path.
    readme = readme.replace('**[Download the template ZIP](../website/dist/submission-template.zip)**',
                            '**This directory is the submission template.**')
    files = {'submission/submission.json':encode(manifest),
        'submission/queries.json':encode(reference),
        'submission/validate.py':(HERE/'validate.py').read_bytes(),
        'submission/README.md':readme.encode('utf-8'),
        'submission/reports/README.md':b'Place reports here as <query_id>.md. See submission.json for all 40 exact filenames. No example report counts as a system output.\n'}
    out = REPO / 'website/dist/submission-template.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026,11,17,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return dict(queries=len(queries), template_sha256=hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == '__main__':
    print(json.dumps(build()))

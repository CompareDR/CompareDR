"""Validate a CompareDR intake directory offline; never judge or execute reports."""
import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUERYSET_SHA256 = '5867ff2f04dca800d2390cf017e056f778c948f92042964083a0d45d813baf96'


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root, fill_hashes=False):
    root = Path(root).resolve()
    require(root.is_dir(), 'Expected an unzipped submission directory')
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Symlinks are not allowed in a submission')
    manifest_path = root / 'submission.json'
    data = load(manifest_path)
    require(isinstance(data, dict), 'submission.json must contain a JSON object')
    require(sha(HERE / 'queries.json') == QUERYSET_SHA256, 'Reference query set has been modified')
    require(sha(root / 'queries.json') == QUERYSET_SHA256, 'Query set differs from the distributed template')
    reference = load(HERE / 'queries.json')
    require(data.get('schema_version') == '1.0', 'Unsupported schema_version')
    require(data.get('benchmark') == 'CompareDR' and data.get('query_set') == 'comparedr-40', 'Incorrect benchmark/query_set')
    require(data.get('permission_to_evaluate') is True, 'Confirm permission_to_evaluate before submission')
    require(isinstance(data.get('redistribution_notes'), str) and data['redistribution_notes'].strip(), 'Describe redistribution permission or restrictions')
    system = data.get('system')
    require(isinstance(system, dict), 'Missing system metadata')
    for key in ('name', 'model', 'harness', 'reasoning', 'generation_start', 'generation_end'):
        require(isinstance(system.get(key), str) and system[key].strip(), 'Missing system.' + key)
    start = datetime.date.fromisoformat(system['generation_start'])
    end = datetime.date.fromisoformat(system['generation_end'])
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',system['generation_start']) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',system['generation_end']), 'Use YYYY-MM-DD dates')
    require(start <= end, 'Generation date range is reversed')
    require(isinstance(system.get('settings'), dict) and system['settings'], 'Provide a nonempty system.settings object')
    records = data.get('reports')
    require(isinstance(records, list) and len(records) == 40, 'Manifest must contain all 40 task records')
    require(all(isinstance(r, dict) and isinstance(r.get('query_id'), str) for r in records), 'Invalid report records')
    ids = [r['query_id'] for r in records]
    expected = {q['query_id'] for q in reference['queries']}
    require(len(set(ids)) == 40 and set(ids) == expected, 'Duplicate, missing, or unknown query IDs')
    completed = 0
    warnings = []
    failed = []
    allowed_reports = set()
    for row in records:
        qid = row['query_id']
        if row.get('status') == 'failed':
            require(row.get('report_path') is None and row.get('sha256') is None, qid + ': failed task must have null report_path and sha256')
            require(isinstance(row.get('error'), str) and row['error'].strip(), qid + ': describe the failure')
            failed.append(qid)
            continue
        require(row.get('status') == 'completed', qid + ': status must be completed or failed')
        rel = 'reports/' + qid + '.md'
        require(row.get('report_path') == rel, qid + ': use reports/<query_id>.md')
        path = root / rel
        require(path.is_file() and path.resolve().is_relative_to(root), qid + ': missing or unsafe report')
        text = path.read_text(encoding='utf-8')
        require(text.strip() and '\x00' not in text, qid + ': empty or binary report')
        digest = sha(path)
        if fill_hashes:
            row['sha256'] = digest
        require(row.get('sha256') == digest, qid + ': SHA-256 mismatch; use --fill-hashes after finalizing files')
        allowed_reports.add(path.resolve())
        completed += 1
        if not re.search(r'https?://\S+', text):
            warnings.append({'query_id': qid, 'warning': 'No external citation URL detected; requires manual review'})
    for path in (root / 'reports').glob('*.md'):
        if path.name != 'README.md':
            require(path.resolve() in allowed_reports, 'Unexpected/unbound report file: ' + path.name)
    if fill_hashes:
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return dict(status='format_valid' if not failed else 'incomplete', completed_reports=completed,
                expected_reports=40, failed_queries=failed, warnings=warnings,
                ready_for_maintainer_review=not failed, api_calls=0,
                scope='Format and file integrity only; not content acceptance, privacy certification, or leaderboard admission')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--fill-hashes', action='store_true', help='Update only report SHA-256 values in submission.json')
    args = parser.parse_args()
    try:
        result = validate(args.directory, args.fill_hashes)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'status': 'invalid', 'error': str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'format_valid' else 2)


if __name__ == '__main__':
    main()

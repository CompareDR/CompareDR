"""Offline MiniMax intake. Preserve prose; attach numbered citations by code.

No network, model, graph extraction, scoring, or changes to a frozen evaluator.
`install(common, manifest)` is explicitly opt-in for a future MiniMax batch.
"""
import argparse
import copy
import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

VERSION = 'minimax-numbered-citations-v1'
DEFAULT_EVALUATOR = Path(__file__).resolve().parent
ENTRY = re.compile(r'^ {0,3}(?:【(?P<ch>\d+)】|\[(?P<en>\d+)\])(?![\[(])', re.M)
ATOM = r'(?:【[\d ,，;；\t–—\-~至]+】|\[[\d ,，;；\t–—\-~至]+\])'
MARKER = re.compile(ATOM + r'(?:[ \t]*[–—\-~至][ \t]*' + ATOM + r')?')
DELIVERY = re.compile(r'<deliver-assets>\s*(?:<media\b[^>]*?/\s*>\s*)+</deliver-assets>', re.S)


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_text(value):
    return sha_bytes(value.encode('utf-8'))


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def code_ranges(text):
    """Markdown fences and inline code; their labels are not citations/UI."""
    ranges = []
    opened = None
    pos = 0
    for line in text.splitlines(keepends=True):
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line.rstrip('\r\n'))
        if opened:
            if m and m[1][0] == opened[1] and len(m[1]) >= opened[2] and not m[2].strip():
                ranges.append((opened[0], pos + len(line)))
                opened = None
        elif m:
            opened = (pos, m[1][0], len(m[1]))
        pos += len(line)
    if opened:
        ranges.append((opened[0], len(text)))
    for m in re.finditer(r'(`+)(?!`).*?(?<!`)\1(?!`)', text):
        if not any(a <= m.start() < b for a, b in ranges):
            ranges.append(m.span())
    return sorted(ranges)


def excluded(pos, ranges):
    return any(a <= pos < b for a, b in ranges)


def cleanup(text):
    """Delete only delivery metadata, with exact reversible edit receipts."""
    spans = code_ranges(text)
    removals = [(m.start(), m.end(), 'ui_delivery_markup') for m in DELIVERY.finditer(text)
                if not excluded(m.start(), spans)]
    temp = text
    for a, b, _ in reversed(removals):
        temp = temp[:a] + temp[b:]
    heading = re.search(r'^#\s+\S', temp, re.M)
    # Only a known delivery-only prologue may be discarded, never an arbitrary
    # executive summary or other substantive material preceding the first H1.
    delivery_lines = [
        r"The report is complete\. Here's the final deliverable:",
        r"Here's the full banquet plan, with the deliverable file attached\.",
        r"Here's the research report:",
        r"The report has been written\. Here it is:",
        r"Here is the final research report:",
        r"Here's the compiled report on .+",
        r'报告已生成完毕[,，].*以下是完整内容.*',
        r'完成。最终报告已写入 `/workspace/[^`]+`，整个工作区只含这一份文件。',
        r'下面是报告的完整内容[:：]',
        r'下面是完整调研结果，已按你的要求.*',
        r'调研报告已完成，按.*四个部分组织.*',
        r"Now I'll return the final answer content to the user\.",
    ]
    warnings = []
    if heading:
        prefix = temp[:heading.start()]
        lines = [s.strip() for s in prefix.splitlines() if s.strip() and s.strip() != '---']
        recognized = lines and all(any(re.fullmatch(p, s) for p in delivery_lines) for s in lines)
        if recognized or (not lines and any(a < text.find('# ') for a, _, _ in removals)):
            original_heading = next(m.start() for m in re.finditer(r'^#\s+\S', text, re.M)
                                    if not excluded(m.start(), spans))
            removals = [(a, b, why) for a, b, why in removals if a >= original_heading]
            removals.append((0, original_heading, 'delivery_only_prologue'))
        elif lines:
            warnings.append('Unrecognized pre-title text preserved')
    removals.sort()
    edits = [{'start': a, 'end': b, 'removed_text': text[a:b], 'reason': why}
             for a, b, why in removals]
    cleaned = text
    for e in reversed(edits):
        cleaned = cleaned[:e['start']] + cleaned[e['end']:]
    if not cleaned.strip():
        raise ValueError('Cleanup would remove the report')
    if re.search(r'</?(?:deliver-assets|media)\b', cleaned):
        warnings.append('Non-delivery or code-quoted UI tag preserved')
    assert restore(cleaned, edits) == text
    return cleaned, edits, warnings


def restore(cleaned, edits):
    """Restore the byte-equivalent UTF-8 input using deletion-only receipts."""
    original = cleaned
    for e in edits:
        original = original[:e['start']] + e['removed_text'] + original[e['start']:]
    return original


def url_spans(text, offset=0):
    out = []
    # Chinese punctuation and prose semicolons delimit bibliography URLs.
    for m in re.finditer(r'https?://[^\s<>"`，。；、（）【】;]+', text):
        value = m[0].rstrip('.,:')
        while value.endswith(')') and value.count(')') > value.count('('):
            value = value[:-1]
        while value.endswith(']') and value.count(']') > value.count('['):
            value = value[:-1]
        if value:
            out.append({'url': value, 'start': offset + m.start(), 'end': offset + m.start() + len(value)})
    return out


def bibliography(text):
    spans = code_ranges(text)
    matches = [m for m in ENTRY.finditer(text) if not excluded(m.start(), spans)]
    headings = []
    for m in re.finditer(r'^.*(?:参考|References|Bibliography|Sources).*$' , text, re.M | re.I):
        title = re.sub(r'^[ #*\t]+|[ #*\t]+$', '', m[0])
        title = re.sub(r'^[一二三四五六七八九十\d]+[、.．:：]\s*', '', title)
        if re.fullmatch(r'参考(?:资料|文献|来源)?|References|Bibliography|Sources', title, re.I) and not excluded(m.start(), spans):
            headings.append(m.end())
    if headings:
        start = headings[-1]
        chosen = [m for m in matches if m.start() >= start]
        detection = 'explicit_bibliography_heading'
    else:
        runs = []
        for m in matches:
            n = int(m['ch'] or m['en'])
            if n == 1:
                runs.append([])
            if runs:
                runs[-1].append(m)
        chosen = []
        for run in reversed(runs):
            nums = [int(m['ch'] or m['en']) for m in run]
            if len(run) >= 2 and nums == list(range(1, len(nums) + 1)):
                chosen = run
                break
        start = chosen[0].start() if chosen else len(text)
        detection = 'ordered_tail_bibliography' if chosen else 'not_found'
    entries = []
    for m in chosen:
        line_end = text.find('\n', m.end())
        end = len(text) if line_end < 0 else line_end + 1
        # Wrapped entries continue to a blank line, heading, or next entry.
        while end < len(text):
            next_end = text.find('\n', end)
            next_end = len(text) if next_end < 0 else next_end + 1
            line = text[end:next_end]
            if not line.strip() or ENTRY.match(line) or re.match(r'^#{1,6}\s|^---\s*$', line):
                break
            end = next_end
        urls = url_spans(text[m.start():end], m.start())
        urls = list({u['url']: u for u in urls}.values())
        entries.append({'label': str(int(m['ch'] or m['en'])), 'start': m.start(), 'end': end,
                        'text': text[m.start():end], 'urls': urls})
    # Without a heading, a final numbered sequence must actually look like
    # references, not an arbitrary [1]/[2] answer list. Uncertain cases stay raw.
    if detection == 'ordered_tail_bibliography' and sum(bool(e['urls']) for e in entries) < len(entries) / 2:
        return len(text), [], 'not_found'
    return start, entries, detection


def labels(marker):
    inner = marker.translate(str.maketrans({'【': '', '】': '', '[': '', ']': ''}))
    result = []
    for part in re.split(r'[,，;；]', inner):
        m = re.fullmatch(r'\s*(\d+)\s*([–—\-~至])\s*(\d+)\s*', part)
        if m:
            lo, hi = int(m[1]), int(m[3])
            if hi < lo or hi - lo > 512:
                return []
            result.extend(str(n) for n in range(lo, hi + 1))
        else:
            result.extend(str(int(n)) for n in part.split() if n.isdigit())
    return list(dict.fromkeys(result))


def enrich(text, doc, units):
    """Use bibliography URL offsets but own the citation in its BODY block."""
    start, entries, detection = bibliography(text)
    by_label = {}
    for entry in entries:
        by_label.setdefault(entry['label'], []).append(entry)
    duplicates = [label for label, values in by_label.items() if len(values) != 1]
    spans = code_ranges(text) + [(u['start'], u['end']) for u in url_spans(text)]
    occurrences = []
    for m in MARKER.finditer(text[:start]):
        # Existing Markdown links/reference links remain owned by base_prepare.
        if excluded(m.start(), spans) or text[m.end():m.end()+1] in ('(', '['):
            continue
        if m.start() and text[m.start()-1] == '\\':
            continue
        occurrence = {'start': m.start(), 'end': m.end(), 'marker': m[0], 'labels': labels(m[0]),
                      'citation_ids': [], 'unresolved': []}
        block = next((b for b in doc['blocks'] if b['start'] <= m.start() < b['end']), None)
        if block is None or block['kind'] in ('code', 'whitespace'):
            continue
        occurrence['block_id'] = block['id']
        for label in occurrence['labels']:
            values = by_label.get(label, [])
            if len(values) != 1 or not values[0]['urls']:
                reason = 'missing_entry' if not values else 'duplicate_entry' if len(values) != 1 else 'no_explicit_url'
                occurrence['unresolved'].append({'label': label, 'reason': reason})
                continue
            entry = values[0]
            for url in entry['urls']:
                cid = f"U{len(doc['citations']) + 1:04d}"
                citation = {'id': cid, 'block_id': block['id'], **url,
                            'format': 'numbered_bibliography', 'reference_label': label,
                            'marker_start': m.start(), 'marker_end': m.end(),
                            'definition_start': entry['start'], 'definition_end': entry['end'],
                            'candidate_scope': 'numbered_reference_entry',
                            'multiple_urls_in_entry': len(entry['urls']) > 1,
                            'support_verified': False}
                assert text[citation['start']:citation['end']] == citation['url']
                doc['citations'].append(citation)
                block['citation_ids'].append(cid)
                occurrence['citation_ids'].append(cid)
        occurrences.append(occurrence)
    added = [c for c in doc['citations'] if c.get('format') == 'numbered_bibliography']
    blocks = {b['id']: b for b in doc['blocks']}
    for unit in units:
        if unit['kind'] == 'table_row':
            header = blocks[unit['parent_id']]['rows'][0]
            extra = [c['id'] for c in added if c['block_id'] == unit['parent_id'] and
                     (unit['start'] <= c['marker_start'] < unit['end'] or
                      header['start'] <= c['marker_start'] < header['end'])]
            unit['citation_ids'] = list(dict.fromkeys(unit['citation_ids'] + extra))
        else:
            unit['citation_ids'] = list(blocks[unit['id']]['citation_ids'])
    doc['numbered_reference_diagnostics'] = {
        'version': VERSION, 'detection': detection, 'entries': entries,
        'duplicate_labels': duplicates, 'occurrences': occurrences,
        'entries_without_urls': [e['label'] for e in entries if not e['urls']],
        'policy': 'Explicit candidate attribution only; no support claim, search, inferred URL, or first-URL selection',
    }
    assert ''.join(b['text'] for b in doc['blocks']) == text
    assert len({c['id'] for c in doc['citations']}) == len(doc['citations'])
    return doc, units


def prepare(text, base_prepare):
    # Cleanup is a distinct intake operation. Prepare only annotates its EXACT
    # input, so original_text, quotes and source offsets stay mutually consistent.
    return enrich(text, *base_prepare(text))


def install(common, manifest_path):
    """Opt-in prepared-input loader. All non-MiniMax inputs remain unchanged."""
    manifest_path = Path(manifest_path).resolve()
    manifest = load(manifest_path)
    if manifest['adapter_sha256'] != sha_bytes(Path(__file__).read_bytes()):
        raise ValueError('Adapter changed after intake freeze; create a new intake version')
    expected = manifest['evaluator_contract']
    if any(sha_bytes(Path(p).read_bytes()) != h for p, h in expected.items()):
        raise ValueError('Frozen preprocessing contract changed')
    if getattr(common.prepare, 'minimax_intake_version', None):
        raise ValueError('MiniMax adapter already installed')
    original = common.prepare
    prepared = {}
    for row in manifest['reports']:
        text = Path(row['path']).read_bytes().decode('utf-8')
        if sha_text(text) != row['sha256']:
            raise ValueError('Prepared MiniMax report changed: ' + row['task_key'])
        objects = []
        for field in ('document', 'units'):
            p = manifest_path.parent / row[field]
            if sha_bytes(p.read_bytes()) != row[field + '_sha256']:
                raise ValueError('Prepared citation sidecar changed: ' + row['task_key'])
            objects.append(load(p))
        prepared[row['sha256']] = objects

    def wrapped(text):
        saved = prepared.get(sha_text(text))
        return tuple(copy.deepcopy(saved)) if saved is not None else original(text)

    wrapped.minimax_intake_version = VERSION
    common.prepare = wrapped
    return original  # A caller/test can explicitly restore the original function.


def build(source, out, evaluator):
    source, out, evaluator = Path(source).resolve(), Path(out).resolve(), Path(evaluator).resolve()
    sys.path.insert(0, str(evaluator))
    common = importlib.import_module('common')
    inputs = load(source / 'batch40.json')
    out.mkdir(parents=True, exist_ok=False)
    contract_files = [Path(common.__file__), Path(common.graph.__file__), Path(common.graph.h.__file__),
                      Path(common.graph.h.old.__file__), Path(common.refs.__file__)]
    manifest = {'version': VERSION, 'adapter_sha256': sha_bytes(Path(__file__).read_bytes()),
                'evaluator_contract': {str(p): sha_bytes(p.read_bytes()) for p in contract_files},
                'collection_manifest': str(source / 'batch40.json'),
                'collection_manifest_sha256': sha_bytes((source / 'batch40.json').read_bytes()),
                'system': 'MiniMax', 'proposed_report_id': 'R10', 'reports': [], 'missing': [],
                'model_calls': 0, 'network_calls': 0, 'scores_generated': 0}
    counts = {'reports': 0, 'ui_cleaned_reports': 0, 'prologue_cleaned_reports': 0,
              'before_citations': 0, 'after_citations': 0, 'bound_body_markers': 0,
              'partly_or_wholly_unresolved_markers': 0, 'entries_without_urls': 0,
              'multi_url_entries': 0, 'units_with_bound_citations': 0}
    for job in inputs['jobs']:
        assert sha_text(job['full_query']) == job['query_sha256']
        frozen_manifest = load(evaluator / 'full40/manifests' / (job['task_key'].replace(':', '_') + '.json'))
        assert load(frozen_manifest['rubrics'])['full_query'] == job['full_query']
        if not job.get('report_dir'):
            manifest['missing'].append({'task_key': job['task_key'], 'query': job['full_query'],
                                        'query_sha256': job['query_sha256'], 'state': job['state'],
                                        'source_url': job['task_url'], 'report': None})
            continue
        original_dir = source / job['report_dir']
        metadata = load(original_dir / 'report.json')
        raw = (original_dir / 'raw.md').read_bytes()
        original_bytes = (original_dir / 'report.md').read_bytes()
        assert sha_bytes(raw) == metadata['raw_sha256']
        assert sha_bytes(original_bytes) == metadata['report_sha256']
        assert metadata['query'] == job['full_query'] and metadata['source_url'] == job['task_url']
        original = original_bytes.decode('utf-8')
        cleaned, edits, warnings = cleanup(original)
        before_doc, _ = common.prepare(cleaned)
        doc, units = prepare(cleaned, common.prepare)
        common.validate_report({'segments': units, 'citations': doc['citations']})
        directory = out / 'reports' / job['task_key'].replace(':', '_')
        directory.mkdir(parents=True)
        (directory / 'report.md').write_bytes(cleaned.encode('utf-8'))
        save(directory / 'document.json', doc)
        save(directory / 'units.json', units)
        save(directory / 'provenance.json', {'version': VERSION, 'source_path': str(original_dir / 'report.md'),
             'source_sha256': metadata['report_sha256'], 'raw_path': str(original_dir / 'raw.md'),
             'raw_sha256': metadata['raw_sha256'], 'prepared_sha256': sha_text(cleaned),
             'edits': edits, 'warnings': warnings, 'reversible_cleanup': restore(cleaned, edits) == original,
             'prose_rewritten': False, 'citation_urls_inferred': False})
        diag = doc['numbered_reference_diagnostics']
        stats = {'before_citations': len(before_doc['citations']), 'after_citations': len(doc['citations']),
                 'body_markers': len(diag['occurrences']),
                 'bound_body_markers': sum(bool(x['citation_ids']) for x in diag['occurrences']),
                 'partly_or_wholly_unresolved_markers': sum(bool(x['unresolved']) for x in diag['occurrences']),
                 'entries_without_urls': len(diag['entries_without_urls']),
                 'multi_url_entries': sum(len(e['urls']) > 1 for e in diag['entries']),
                 'units_with_bound_citations': sum(bool(u['citation_ids']) for u in units)}
        if not stats['bound_body_markers']:
            warnings.append('No resolvable body markers; not treated as cited by this adapter')
        row = {'task_key': job['task_key'], 'query': job['full_query'], 'query_sha256': job['query_sha256'],
               'language': job['language'], 'source_url': job['task_url'], 'system': 'MiniMax',
               'report_id': 'R10', 'path': str(directory / 'report.md'), 'sha256': sha_text(cleaned),
               'original_path': str(original_dir / 'report.md'), 'original_sha256': metadata['report_sha256'],
               'raw_sha256': metadata['raw_sha256'], 'stats': stats, 'warnings': warnings,
               'document': str((directory / 'document.json').relative_to(out)),
               'units': str((directory / 'units.json').relative_to(out)),
               'provenance': str((directory / 'provenance.json').relative_to(out))}
        for field in ('document', 'units'):
            row[field + '_sha256'] = sha_bytes((out / row[field]).read_bytes())
        manifest['reports'].append(row)
        counts['reports'] += 1
        counts['ui_cleaned_reports'] += '<deliver-assets>' in original and '<deliver-assets>' not in cleaned
        counts['prologue_cleaned_reports'] += any(e['reason'] == 'delivery_only_prologue' for e in edits)
        for k in stats:
            if k in counts:
                counts[k] += stats[k]
    manifest['summary'] = counts
    save(out / 'manifest.json', manifest)
    # Exercise the actual Runner-consumed common.prepare hook, without Runner,
    # credentials, prompts, calls or score creation.
    base = install(common, out / 'manifest.json')
    try:
        for row in manifest['reports']:
            text = Path(row['path']).read_bytes().decode('utf-8')
            doc, units = common.prepare(text)
            assert doc == load(out / row['document']) and units == load(out / row['units'])
            common.validate_report({'segments': units, 'citations': doc['citations']})
            payload = common.graph.payload(row['query'], units)
            assert payload['query'] == row['query']
        inherited_reports = 0
        for path in (evaluator / 'full40/manifests').glob('*.json'):
            for r in load(path)['reports']:
                text = Path(r['path']).read_bytes().decode('utf-8')
                assert common.prepare(text) == base(text), 'Existing input altered: ' + str(r)
                inherited_reports += 1
    finally:
        common.prepare = base
    save(out / 'compatibility_check.json', {'prepared_reports': len(manifest['reports']),
         'existing_reports_unchanged': inherited_reports, 'input_hashes_verified': True,
         'cleanups_reversible': True, 'ids_and_url_offsets_valid': True,
         'actual_common_prepare_hook_checked': True, 'model_calls': 0, 'network_calls': 0})
    lines = ['# MiniMax格式兼容检查', '', '| 项目 | 结果 |', '|---|---:|']
    lines += [f'| {k} | {v} |' for k, v in counts.items()]
    lines += ['', f'原九系统输入：{inherited_reports}篇适配前后完全相同。',
              '只恢复编号引用的候选来源归属，不代表来源支持成立；没有URL的参考保留，不猜网址。',
              '原文、Query、Rubrics、模型、Prompt、评分与缓存不改；仅清理已识别的交付标签/前缀。',
              f"{len(manifest['reports'])}份报告与{len(manifest['missing'])}题缺项分别记录，本输入准备步骤未启动评分。", '',
              '| Query | 原引用ID | 适配后引用ID | 绑定正文标记 | 未完全绑定标记 | 无URL参考 |',
              '|---|---:|---:|---:|---:|---:|']
    for row in manifest['reports']:
        s = row['stats']
        lines.append(f"| {row['task_key']} | {s['before_citations']} | {s['after_citations']} | {s['bound_body_markers']} | {s['partly_or_wholly_unresolved_markers']} | {s['entries_without_urls']} |")
    (out / 'CHECK.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(out), **counts, 'existing_reports_unchanged': inherited_reports,
                      'missing': manifest['missing'], 'model_calls': 0}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'prepared')
    parser.add_argument('--evaluator', type=Path, default=DEFAULT_EVALUATOR)
    args = parser.parse_args()
    build(args.source, args.out, args.evaluator)

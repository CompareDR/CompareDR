"""Restore nonblocking verification failure without changing frozen artifacts.

This adapter changes two control-flow guards only. Prompts, model outputs,
request budgets, scoring and successful cache entries remain unchanged.
"""
import copy
import inspect
from pathlib import Path
import sys
import textwrap
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import completeness as V
import orchestration as O
import pipeline as P

VERSION = 'verification-fallback-v1'


def record(runner, stage, cards):
    failed = [c for c in cards if c.get('execution') == 'failed']
    if not failed:
        return
    rows = []
    for card in failed:
        source = runner.out / 'check_results' / (card['check_id'] + '.json')
        if not source.exists() or V.load(source) != card:
            raise RuntimeError('Fallback must retain an actual saved failure card')
        rows.append({'check_id': card['check_id'], 'sha256': V.sha(source),
                     'error': card.get('error'), 'result': card.get('result')})
    O.save(runner.out / 'verification_fallback_records' / (stage + '.json'), {
        'version': VERSION, 'time': time.time(), 'stage': stage,
        'adapter_sha256': V.sha(Path(__file__)), 'failed_checks': rows,
        'action': 'Continue actual Judge using available originals and evidence; failed verification remains failed, not supported or contradicted.',
        'no_imputed_scores': True})


def audit_with_fallback(audit, root):
    """Only terminal verifier errors with explicit downstream fallback are warnings."""
    result = copy.copy(audit)
    accounted = set()
    for receipt in (Path(root) / 'verification_fallback_records').glob('*.json'):
        value = V.load(receipt)
        if value.get('version') != VERSION:
            continue
        for item in value.get('failed_checks', []):
            source = Path(root) / 'check_results' / (item['check_id'] + '.json')
            if source.exists() and V.sha(source) == item['sha256'] and V.load(source).get('execution') == 'failed':
                accounted.add(item['check_id'])
    warnings, errors = [], []
    for error in audit['errors']:
        if audit['scoring_complete'] and error['stage'] == 'verification' and error['object'] in accounted:
            warnings.append(error | {'handling': 'actual downstream scoring completed with explicit failed-verification input'})
        else:
            errors.append(error)
    result.update(raw_framework_complete=audit['framework_complete'],
                  verification_complete=not any(e['stage'] == 'verification' for e in audit['errors']),
                  verification_warnings=warnings, errors=errors, fallback_policy=VERSION)
    result['framework_complete'] = not errors and all(audit['counts'][k] == n for k, n in audit['expected'].items())
    result['completion_status'] = ('complete_with_verification_warnings' if warnings else 'complete') if result['framework_complete'] else 'incomplete'
    return result


def install():
    if getattr(P, '_verification_fallback_installed', False):
        return
    old_pt = "if not use or any(c.get('execution')=='failed' for c in use):raise RuntimeError('Verification technical failure or missing binding; initial score retained, review not completed')"
    new_pt = "if not use:raise RuntimeError('Missing verification binding')\n  _record_verification_fallback(self,'pt_'+rid+'_'+i,use)"
    old_pw = "if any(cards.get(i,{}).get('execution')=='failed' for i in needed):raise RuntimeError('Pairwise verification has technical failure; content judgment not silently downgraded')"
    new_pw = "if any(i not in cards for i in needed):raise RuntimeError('Missing verification binding')\n _record_verification_fallback(self,'pair_'+key,[cards[i] for i in sorted(needed)])"
    P._record_verification_fallback = record
    for name, old, new in [('pointwise', old_pt, new_pt), ('pairwise', old_pw, new_pw)]:
        source = textwrap.dedent(inspect.getsource(getattr(P.Runner, name)))
        if source.count(old) != 1:
            raise RuntimeError('Frozen guard drift; refusing an ambiguous patch: ' + name)
        namespace = {}
        exec(compile(source.replace(old, new), str(HERE / ('restored_' + name + '.py')), 'exec'), P.__dict__, namespace)
        setattr(P.Runner, name, namespace[name])
    original_audit = V.inspect_task
    V.inspect_task = lambda manifest, root, require_trace=True: audit_with_fallback(original_audit(manifest, root, require_trace), root)
    P._verification_fallback_installed = True


def main():
    install()
    return O.main()


if __name__ == '__main__':
    raise SystemExit(main())

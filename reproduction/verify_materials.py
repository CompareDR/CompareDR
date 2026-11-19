"""Verify the selected report bodies and their exact label bindings, offline."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def require(condition,message):
    if not condition:raise ValueError(message)

def read(relative):
    path=ROOT/relative
    require(not path.is_symlink() and path.resolve().is_relative_to(ROOT.resolve()),'Unsafe material input path')
    return json.loads(path.read_text(encoding='utf-8'))

def verify():
    manifest=read('materials/MANIFEST.json')
    packet=read(manifest['selected_labels']);rows=manifest['files']
    require(len(rows)==160 and len(packet['cases'])==40 and len(packet['labels'])==120, 'Material integrity check failed at condition 14')
    require(Counter(r['kind'] for r in rows)=={'base':40,'improve':40,'degrade':40,'equivalent':40}, 'Material integrity check failed at condition 15')
    index={(r['case_id'],r['kind']):r for r in rows}
    require(len(index)==160, 'Material integrity check failed at condition 17')
    paths=set()
    for row in rows:
        path=ROOT/row['path'];relative=path.resolve().relative_to(ROOT.resolve())
        require(relative.parts[:2]==('materials','controlled_revisions') and not path.is_symlink(), 'Material integrity check failed at condition 21')
        require(relative not in paths, 'Material integrity check failed at condition 22');paths.add(relative)
        require(hashlib.sha256(path.read_bytes()).hexdigest()==row['file_sha256'], str(relative))
    require(not any(p.is_symlink() for p in (ROOT/'materials/controlled_revisions').rglob('*')),'Unexpected report symlink')
    actual={p.relative_to(ROOT) for p in (ROOT/'materials/controlled_revisions').rglob('*') if p.is_file()}
    require(paths==actual, 'Unexpected or missing report files.')
    labels={(r['case_id'],r['direction']):r for r in packet['labels']}
    require(len(labels)==120, 'Material integrity check failed at condition 27')
    for case in packet['cases']:
        base=index[case['case_id'],'base']
        require((base['query_id'],base['report_id'],base['sha256'])==(
            case['query_id'],case['mother_report_id'],case['mother_sha256']), 'Material integrity check failed at condition 30')
        plans={p['kind']:p['target_dimension'] for p in case['plans']}
        for variant in case['variants']:
            key=(case['case_id'],variant['kind']);body=index[key];label=labels[key]
            require((body['report_id'],body['query_id'],body['sha256'])==(
                variant['report_id'],case['query_id'],variant['sha256']), 'Material integrity check failed at condition 35')
            require((label['revision_id'],label['revision_sha256'],label['base_sha256'],label['query_id'])==(
                body['report_id'],body['sha256'],base['sha256'],case['query_id']), 'Material integrity check failed at condition 37')
            expected=sorted({plans[k] for k in ('improve','degrade')}) if variant['kind']=='equivalent' else [plans[variant['kind']]]
            require(label['targets']==expected, 'Material integrity check failed at condition 40')
    origin=read('materials/REPORT_ORIGIN.json')
    protocol=read(origin['protocol'])
    require(protocol['plan_review']['reviewers']==3, 'Material integrity check failed at condition 43')
    require(protocol['implementation']['agent']=='Codex Astra', 'Material integrity check failed at condition 44')
    require(protocol['final_review']['type']=='human', 'Material integrity check failed at condition 45')
    require(protocol['direction_labels_status']=='human_confirmed', 'Material integrity check failed at condition 46')
    require(len(origin['cases'])==40, 'Material integrity check failed at condition 47')
    benchmark=read('offline/data/benchmark.json')
    main={(r['query'],r['report_id']):r for r in benchmark['report_manifest']}
    different=[]
    for case in origin['cases']:
        cid=case['case_id'];base=case['base'];archived=index[cid,'base']
        require((base['report_path'],base['sha256'],base['controlled_report_id'])==(
            archived['path'],archived['sha256'],archived['report_id']), 'Material integrity check failed at condition 53')
        require(base['file_sha256']==archived['file_sha256'], 'Material integrity check failed at condition 55')
        same=main[case['query_id'],base['controlled_report_id']]['sha256']==base['sha256']
        require(case['base_matches_main_table_report']==same, 'Material integrity check failed at condition 57')
        if not same:different.append(cid)
        for variant in case['variants']:
            r=index[cid,variant['direction']]
            require((variant['report_path'],variant['sha256'],variant['controlled_report_id'])==(
                r['path'],r['sha256'],r['report_id']), 'Material integrity check failed at condition 61')
            require(variant['file_sha256']==r['file_sha256'], 'Material integrity check failed at condition 63')
            require(variant['target_dimensions']==labels[cid,variant['direction']]['targets'], 'Material integrity check failed at condition 64')
    require(set(different)=={'P003','P010','P013','P019','P028','P030','P032','P043','P048',
                            'P055','P056','P057','P058','P059','P060','P061','P062','P063','P064','P065'}, 'Material integrity check failed at condition 65')
    return {'status':'passed','bases':40,'revisions':120,'label_rows':120,
            'target_dimension_judgments':sum(len(r['targets']) for r in labels.values()),
            'original_evaluation_hashes_match_labels':True,'distributed_file_hashes_verified':True,
            'report_origin_records_verified':40,
            'experiment_specific_base_versions':different,'paper_procedure_matches':True}

if __name__=='__main__':print(json.dumps(verify(),indent=2))

"""Fixed arithmetic only; no judge calls, invented ties or missing-item reweighting."""
import itertools
from completeness import judgments, point_rows, report_set, valid_pair
from settings import SYSTEMS, config

DIMS=('D1','D2','D3','D4','D5','D6')
FIVE=('D1','D2','D3','D4','D5_D6')
def mean(values):return sum(values)/len(values) if values else None

def aggregate(suite,reports,points,pairs,cards):
    report_set(reports)
    guides={g['id']:g for g in suite['pairwise']}; dims={r['id']:r['dimension'] for r in suite['pointwise']}
    expected={tuple(p) for p in itertools.combinations(SYSTEMS,2)}; actual={};errors=[];agreements=[];reversals=0
    for pair in pairs:
        key=tuple(pair.get('report_ids',[]))
        if key not in expected or key in actual:raise ValueError('Unexpected/duplicate pair: '+str(key))
        try:valid_pair(pair,guides,key)
        except (KeyError,ValueError,TypeError) as ex:errors.append(str(ex));continue
        actual[key]=pair
        aa={r['guide_id']:r for r in pair['AB']['judgments']};bb={r['guide_id']:r for r in pair['BA']['judgments']}
        for g in guides:
            x,y=aa[g]['preferred_report_id'],bb[g]['preferred_report_id'];agreements.append(x==y)
            reversals+=x!='tie' and y!='tie' and x!=y
    gate=set(actual)==expected and not errors
    rows={}; weights=config()['weights'];den=sum(weights)
    for report in reports:
        rid=report['report_id'];pd=points.get(rid,{}).get('final',{});row={}
        if rid in points:point_rows(points[rid],dims)
        for dim in DIMS:
            pids=[i for i,d in dims.items() if d==dim]; gids=[i for i,g in guides.items() if g['dimension']==dim]
            ptok=all(i in pd for i in pids);pv=mean([pd[i]['score'] for i in pids]) if ptok else None
            margins=[]
            if gate:
                for key,pair in actual.items():
                    if rid not in key:continue
                    for order in ('AB','BA'):
                        for j in pair[order]['judgments']:
                            if j['guide_id'] in gids:margins.append(j['strength']*(0 if j['preferred_report_id']=='tie' else 1 if j['preferred_report_id']==rid else -1))
            expected_pw=2*(len(reports)-1)*len(gids)
            w=mean(margins) if len(margins)==expected_pw else None
            lanes=([(pv-1)*25] if pv is not None else [])+([(w+2)*25] if w is not None else [])
            score=mean(lanes) if ptok and (not gids or gate) else None
            row[dim]={'pointwise_1_5':pv,'pointwise_scored':sum(i in pd for i in pids),'pointwise_expected':len(pids),
                      'pairwise_minus2_2':w,'pairwise_received':len(margins),'pairwise_expected':expected_pw,'combined_0_100':score}
        ds=[row[d]['combined_0_100'] for d in DIMS]; five=total=None
        if all(v is not None for v in ds):
            five=ds[:4]+[mean(ds[4:])];total=sum(v*w for v,w in zip(five,weights))/den
        rows[rid]={'system':report['system'],'dimensions':row,'five_dimensions':five,'total':total}
    from common import support_fraction
    for rid,row in rows.items():row['support']=support_fraction([c for c in cards if c.get('report_id')==rid])
    return {'aggregation_protocol':'Per-task diagnostic only; PT/PW lane mean; D5/D6 mean; weights30/30/10/10/20; AB/BA arithmetic mean. Use run.py aggregate for final ordinal scores.',
            'direction_agreement':{'agree':sum(agreements),'total':len(agreements),'rate':mean(agreements),'strict_reversals':reversals,'gating_enabled':False,'eligible_for_mean':gate},
            'expected_pairs':len(expected),'received_pairs':len(actual),'missing_pairs':[list(k) for k in sorted(expected-set(actual))],
            'rows':rows,'errors':errors,'total_status':'available' if all(r['total'] is not None for r in rows.values()) else 'incomplete',
            'warning':'Support fraction is diagnostic only. Available scores do not certify completion of all upstream stages.'}

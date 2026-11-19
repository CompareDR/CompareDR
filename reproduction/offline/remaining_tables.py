"""Independent offline implementation of the remaining four table protocols.

Query metadata comes from archived per-query records. Revision labels and report
identities are the matching version selected and confirmed by the author.
"""
from collections import Counter
import hashlib
import math

LABELS = ('degrade', 'equivalent', 'improve')
DIMS = ('D1', 'D2', 'D3', 'D4', 'D5_D6')
CONTROLLED_TABLES = ('tab:controlled_response', 'tab:controlled_thresholds', 'tab:controlled_dimensions')

def predict(signals, tau):
    assert tau >= 0 and math.isfinite(tau)
    assert all(math.isfinite(x) for x in signals)
    return ['improve' if x > tau else 'degrade' if x < -tau else 'equivalent' for x in signals]

def percentage(delta, base):
    if not math.isfinite(base) or base == 0:
        raise ValueError('Percentage difference requires a finite, nonzero base score.')
    return 100 * delta / abs(base)

def optimize(signals, labels, objective, metric):
    assert objective in ('accuracy','macro_f1')
    secondary='macro_f1' if objective=='accuracy' else 'accuracy'
    candidates=sorted({0.,*(abs(x) for x in signals)})
    evaluated=[(t,metric(labels,predict(signals,t),LABELS)) for t in candidates]
    t,m=max(evaluated,key=lambda v:(v[1][objective],v[1][secondary],-v[0]))
    next_boundary=next((x for x in candidates if x>t),None)
    return {'threshold_boundary':t,'regime_upper_exclusive':next_boundary,
            'objective':objective,'secondary':secondary,'metrics':m,
            'distinct_prediction_regimes':len(candidates)}

def targets(case, kind):
    plans={p['kind']:p for p in case['plans']}
    if kind=='equivalent':
        return sorted({plans[k]['target_dimension'] for k in ('improve','degrade')})
    return [plans[kind]['target_dimension']]

def assert_unique(rows, key):
    keys=[key(r) for r in rows]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate item identity; refusing silent overwrite.')

def reconstruct_groups(native, mapping):
    """Subtract archived candidate/base scores; no paper values enter this join."""
    rows=native['baseline_native_scores']
    assert_unique(rows,lambda r:(r['case_id'],r['method'],r['slot']))
    lookup={(r['case_id'],r['method'],r['slot']):r for r in rows}
    out={name:[] for name in ('Full framework','Same-coverage PT','RACE','Source protocols')}
    for c in mapping['cases']:
        q=c['query_id']; fw=native['framework_per_query'][q]; base=fw[c['mother_report_id']]
        for v in c['variants']:
            row={'case_id':c['case_id'],'query_id':q,'construction_direction':v['kind'],
                 'mother_report_id':c['mother_report_id'],'variant_report_id':v['report_id'],
                 'revision_sha256':v['sha256']}
            revision=fw[v['report_id']]
            delta6=[a-b for a,b in zip(revision['six_dimensions'],base['six_dimensions'])]
            out['Full framework'].append({**row,'base':base['total'],
                'delta':revision['total']-base['total'],
                'dimensions':dict(zip(DIMS,delta6[:4]+[sum(delta6[4:])/2]))})
            for method,name in [('full_point','Same-coverage PT'),('race','RACE'),('source','Source protocols')]:
                a=lookup.get((c['case_id'],method,'original'))
                b=lookup.get((c['case_id'],method,v['report_id']))
                if a is None or b is None:continue
                dims=None
                if method=='full_point':
                    dims={dim:b['mapped_dimensions'][dim]-a['mapped_dimensions'][dim] for dim in DIMS}
                out[name].append({**row,'base':a['score_100'],'delta':b['score_100']-a['score_100'],
                                  'dimensions':dims})
    return out

def verified_optimum(R, signals, labels, objective, paper_tau, name):
    result=optimize(signals,labels,objective,R.metric)
    observed=R.metric(labels,predict(signals,paper_tau),LABELS)
    R.check('reported threshold optimal:'+name,
        all(abs(observed[k]-result['metrics'][k])<1e-12 for k in ('accuracy','macro_f1')),
        {'paper_tau':paper_tau,'boundary':result['threshold_boundary'],
         'paper_metrics':observed,'optimal_metrics':result['metrics']})
    result['paper_representative_threshold']=paper_tau
    result['paper_predictions_equal_boundary_predictions']=predict(signals,paper_tau)==predict(signals,result['threshold_boundary'])
    return result

def run(R):
    b=R.read('data/benchmark.json'); meta=R.read('data/query_characteristics.json')
    assert_unique(meta['rows'],lambda r:r['query_id'])
    R.check('characteristics exact task coverage',set(r['query_id'] for r in meta['rows'])==set(b['queries']))
    for r in meta['rows']:
        expected=hashlib.sha256(b['rubrics'][r['query_id']]['full_query'].encode()).hexdigest()
        R.check('characteristics full query identity:'+r['query_id'],r['full_query_sha256']==expected)
        R.check('characteristics classification provenance:'+r['query_id'],bool(r['complexity']['origin']))
    distribution={}
    for k,label in [('breadth','Breadth'),('depth','Depth'),('exploration','Exploratory scope')]:
        counts=Counter(r['complexity'][k] for r in meta['rows'])
        R.check('characteristics valid categories:'+k,set(counts)<=set(('low','medium','high')))
        distribution[k]=[counts[v] for v in ('low','medium','high')]
        R.paper_check('tab:query_characteristics',label,distribution[k],0)
        for lang in ('en','zh'):
            actual=Counter(r['complexity'][k] for r in meta['rows'] if r['language']==lang)
            R.check('characteristics archived distribution:'+lang+':'+k,
                    dict(actual)==meta['archived_distribution'][lang]['complexity'][k])
    R.RESULTS['query_characteristics']={'status':'reproduced_from_verified_per_query_metadata',
        'distribution':distribution,'row_count':len(meta['rows']),
        'origin_counts':dict(Counter(r['complexity']['origin'] for r in meta['rows']))}

    mapping=R.read('data/controlled_selected_packet.json'); native=R.read('data/controlled_native_scores.json')
    R.check('selected packet confirmation',mapping['label_type']=='author_confirmed_matched_version')
    R.check('controlled plan exact40 coverage',len(mapping['cases'])==40 and {c['query_id'] for c in mapping['cases']}==set(b['queries']))
    assert_unique(mapping['cases'],lambda c:c['case_id'])
    assert_unique(mapping['labels'],lambda r:(r['case_id'],r['revision_id']))
    confirmed={(r['case_id'],r['revision_id']):r for r in mapping['labels']}
    R.check('controlled author confirmation120 coverage',len(confirmed)==120)
    for c in mapping['cases']:
        R.check('controlled three variants:'+c['case_id'],{v['kind'] for v in c['variants']}==set(LABELS) and len(c['variants'])==3)
        R.check('controlled plan targets valid:'+c['case_id'],all(d in DIMS for k in LABELS for d in targets(c,k)))
        for v in c['variants']:
            row=confirmed[c['case_id'],v['report_id']]
            R.check('author label packet binding:'+c['case_id']+':'+v['report_id'],
                row['direction']==v['kind'] and row['targets']==targets(c,v['kind'])
                and row['revision_sha256']==v['sha256'] and row['base_sha256']==c['mother_sha256']
                and row['query_id']==c['query_id'])
    groups=reconstruct_groups(native,mapping)
    key=lambda r:(r['case_id'],r['construction_direction'])
    for name,rs in groups.items():assert_unique(rs,key)
    # Compare reconstructed deltas against the separately frozen first intake.
    frozen=R.read('data/expected_controlled_deltas.json')
    old={'Full framework':frozen['framework_paired_deltas'],
         'Same-coverage PT':frozen['paired_mother_deltas']['full_point'],
         'RACE':frozen['paired_mother_deltas']['race'],
         'Source protocols':frozen['paired_mother_deltas']['source']}
    for name,rs in groups.items():
        previous={key(r):r for r in old[name]}
        R.check('controlled raw-score reconstructed coverage:'+name,set(map(key,rs))==set(previous))
        R.check('controlled raw-score reconstructed delta:'+name,
                all(abs(r['delta']-previous[key(r)]['delta'])<1e-10 for r in rs))
    common=set.intersection(*(set(map(key,rs)) for rs in groups.values()))
    R.check('controlled common119 mask',len(common)==119 and set(map(key,groups['Full framework']))-common=={('P049','equivalent')})
    main={};thresholds={};predictions={}
    for name,all_rows in groups.items():
        rows=sorted((r for r in all_rows if key(r) in common),key=key)
        y=[r['construction_direction'] for r in rows];delta=[r['delta'] for r in rows]
        values=R.paper_values('tab:controlled_response',name);tau=values[0]
        optimum=verified_optimum(R,delta,y,'macro_f1',tau,'response:'+name)
        p=predict(delta,tau);m=R.metric(y,p,LABELS);computed=[tau]
        for label in ('improve','degrade','equivalent'):
            n=y.count(label);correct=sum(a==label and z==label for a,z in zip(y,p))
            computed.extend([correct,n,100*correct/n])
        computed.extend([100*m['accuracy'],100*m['macro_f1']])
        R.paper_check('tab:controlled_response',name,computed,[4,0,0,1,0,0,1,0,0,1,1,1])
        main[name]=optimum
        predictions[name]=[{**r,'prediction':z} for r,z in zip(rows,p)]
        threshold_row=R.paper_values('tab:controlled_thresholds',name)
        output_values=[];method_search={}
        for mode,signals in [('absolute',delta),('percentage',[percentage(r['delta'],r['base']) for r in rows])]:
            for objective in ('accuracy','macro_f1'):
                index=len(output_values);paper_tau=threshold_row[index+1]
                result=verified_optimum(R,signals,y,objective,paper_tau,mode+':'+objective+':'+name)
                output_values.extend([100*result['metrics'][objective],paper_tau])
                method_search[mode+'_'+objective]=result
        R.paper_check('tab:controlled_thresholds',name,output_values,[1,6]*4)
        thresholds[name]=method_search

    case_index={c['case_id']:c for c in mapping['cases']}; dimension_output={};dimension_predictions={}
    bydim={}
    for name,tau in [('Full framework',4.68),('Same-coverage PT',3.13)]:
        cells=[{'case_id':r['case_id'],'query_id':r['query_id'],
                'construction_direction':r['construction_direction'],'dimension':dim,
                'signal':r['dimensions'][dim],'revision_sha256':r['revision_sha256']}
               for r in groups[name] for dim in targets(case_index[r['case_id']],r['construction_direction'])]
        assert_unique(cells,lambda r:(r['case_id'],r['construction_direction'],r['dimension']))
        R.check('controlled dimension123 coverage:'+name,len(cells)==123 and Counter(r['construction_direction'] for r in cells)=={'improve':40,'degrade':40,'equivalent':43})
        y=[r['construction_direction'] for r in cells];signals=[r['signal'] for r in cells]
        opt=verified_optimum(R,signals,y,'macro_f1',tau,'dimensions:'+name)
        pred=predict(signals,tau)
        bydim[name]={d:[sum(r['construction_direction']==p for r,p in zip(cells,pred) if r['dimension']==d),
                      sum(r['dimension']==d for r in cells)] for d in DIMS}
        bydim[name]['Overall']=[sum(a==z for a,z in zip(y,pred)),len(cells)]
        dimension_output[name]={'optimum':opt,'by_dimension':bydim[name]}
        dimension_predictions[name]=[{**r,'prediction':p} for r,p in zip(cells,pred)]
    for dim,label in zip((*DIMS,'Overall'),('Responsiveness','Evidence','Reasoning','Synthesis','Readability','Overall')):
        n=bydim['Full framework'][dim][1];values=[n]
        for name in ('Full framework','Same-coverage PT'):
            ok,den=bydim[name][dim];values.extend([ok,den,100*ok/den])
        R.paper_check('tab:controlled_dimensions',label,values,[0,0,0,1,0,0,1])
    R.check('controlled dimension macroF1 prose',
        [round(100*dimension_output[n]['optimum']['metrics']['macro_f1'],1) for n in ('Full framework','Same-coverage PT')]==[56.2,39.4])
    R.RESULTS['controlled_reproduction']={
        'status':'all_three_tables_reproduced_with_author_attested_plan_labels',
        'annotation_provenance':'author_confirmed_matched_version',
        'new_annotation_study_performed':False,'author_confirmation_accepted':True,
        'common_revision_count':119,'target_dimension_count':123,'base_count':40,
        'main_table':main,'threshold_table':thresholds,'dimension_table':dimension_output,
        'predictions':predictions,'dimension_predictions':dimension_predictions,
        'excluded_common_comparison':[{'case_id':'P049','kind':'equivalent','reason':'source protocol score missing'}],
        'calibration':'Within-set threshold optimization, not held-out accuracy.',
        'implementation':'New independent numeric implementation; original scoring results are unchanged.'}

def table_statuses(R):
    matched={c['check'].split(':',2)[0]+':'+c['check'].split(':',2)[1]
             for c in R.CHECKS if c['passed'] and c['check'].startswith('tab:')}
    return {t:('reproduced_with_author_attested_labels' if t in CONTROLLED_TABLES
               else 'reproduced_from_archived_inputs') for t in sorted(matched)}

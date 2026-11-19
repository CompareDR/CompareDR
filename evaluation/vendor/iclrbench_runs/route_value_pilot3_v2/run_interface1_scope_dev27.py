"""Same frozen inputs, one general locator scope clarification; no graph edits."""
import concurrent.futures as cf
import itertools
import statistics
from pathlib import Path
from run_graph_rubric_ablation_dev25 import BASE, DEST as OLD, CONFIG, LOCATION_PROMPT, location_validate, expand, transport

DEST=BASE/'interfaces/interface1_scope_dev27'
PROMPT=LOCATION_PROMPT+'''
Scope discipline for each region: in located_content identify the specific author-stated content relevant to the supplied comparison question, not every topic in a selected composite node or paragraph. In alignment_reason explain that relevance using the content on each side; a merely hypothetical consequence supplied by you is not an author-stated connection. Relevant qualitative reasoning is allowed and need not contain numbers or use the same method. Preserve complete paragraphs/tables as context, but in limit distinguish surrounding content from the specific content being located. Do not infer that everything in the retained table bears on this question. Do not add another field, scoring step, or a prescribed set of regions.'''

def run():
    transport.BASE=DEST
    transport.config=lambda:CONFIG
    sources={c:OLD/'locations'/f'{c}_r1'/'input.json' for c in ['query_only','query_plus_question']}
    inputs={c:transport.load(p) for c,p in sources.items()}
    transport.freeze(DEST/'protocol.json',{'prompt':PROMPT,'config':CONFIG,'calls':6,
        'source_sha256':{c:transport.sha(p) for c,p in sources.items()},
        'baseline':'interface1_fixed_dev26','change':'General scope clarification only; same schema and originals/graphs.',
        'selection':'Same first graph pair per condition as baseline; three independent locator repeats.',
        'code_sha256':transport.sha(Path(__file__)),
        'limits':'Single-case development diagnostic, not generalization or graph-vs-fulltext evidence.',
        'no_input_repairs':True})
    def call(c,n):
        folder=DEST/'locations'/f'{c}_r{n}';data=inputs[c]
        transport.freeze(folder/'input.json',data)
        if (folder/'status.json').exists():return
        transport.save(folder/'status.json',{'state':'running'})
        try:
            result=transport.Client().call(f'dev27_{c}_{n}',PROMPT,data,location_validate,'en','interface1')
            transport.freeze(folder/'output.json',result)
            transport.freeze(folder/'expanded.json',expand(result['result'],data))
            status={'state':'complete_pending_semantic_review','usage':result['usage'],'returned_model':result['returned_model']}
        except Exception as e:status={'state':'failed','error':str(e)}
        transport.save(folder/'status.json',status);print(c,n,status,flush=True)
    with cf.ThreadPoolExecutor(max_workers=20) as pool:
        for f in cf.as_completed([pool.submit(call,c,n) for c in inputs for n in range(1,4)]):f.result()
    summary={}
    for c in inputs:
        outputs=[transport.load(p) for p in sorted((DEST/'locations').glob(f'{c}_r*/expanded.json'))]
        overlap={}
        for r in inputs[c]['reports']:
            sets=[{sid.rsplit('-',1)[0] for reg in o['regions'] for side in reg['sides'] if side['report_id']==r['report_id'] for sid in side['segment_ids']} for o in outputs]
            vals=[len(a&b)/len(a|b) if a|b else 1 for a,b in itertools.combinations(sets,2)]
            overlap[r['report_id']]=statistics.mean(vals) if vals else None
        summary[c]={'completed':len(outputs),'total':3,'region_counts':[len(o['regions']) for o in outputs],'paragraph_jaccard':overlap}
    transport.save(DEST/'summary.json',summary);print(summary,flush=True)

if __name__=='__main__':run()

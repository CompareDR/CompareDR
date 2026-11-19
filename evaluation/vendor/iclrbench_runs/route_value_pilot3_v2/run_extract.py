"""Reuse standalone API transport only, not legacy orchestration or results."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path
from graph_interface import validate_graph

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]/'project'
SOURCE=ROOT/'experiments/query_specific_rubrics_scoring3_v01/client.py'
spec=importlib.util.spec_from_file_location('transport_only',SOURCE)
transport=importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
config=transport.config() | {'max_tokens':18000,'attempts':1,'workers':2}
# Do not invoke legacy batch/prepare/graph/rubric code.
transport.BASE=BASE/'extraction'
transport.config=lambda:config

def run(task,rid,nonce):
    official=json.loads((BASE/'inputs'/task/'official_input.json').read_text())
    report=json.loads((BASE/'inputs'/task/f'{rid}.json').read_text())
    language='en' if task.startswith('rr_') else 'zh'
    prompt=(BASE/'prompts'/f'extract_{language}.md').read_text()
    data={'query':official['full_query'],'report':report}
    name=f'{task}_{rid}_{nonce}'
    # Contract and wrapper hashes belong to cache identity, not the model input.
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [BASE/'graph_interface.py',Path(__file__),SOURCE]}
    contract=transport.digest(hashes)
    transport.freeze(BASE/'extraction'/'configuration.json',config)
    transport.freeze(BASE/'extraction'/'contracts'/f'{contract}.json',hashes)
    def validate(out,data): validate_graph(out,data['report'])
    try:
        result=transport.Client().call(name+'_'+contract,prompt,data,validate,language,'graph_extraction')
        transport.freeze(BASE/'graphs'/nonce/task/f'{rid}.json',result)
        status={'state':'structurally_valid_pending_semantic_review',
                'call_key':result['call_key'],'returned_model':result['returned_model'],'usage':result['usage']}
    except Exception as exc:
        # Raw failed output retained in calls/; no partial graph silently admitted.
        status={'state':'failed','error':str(exc)}
    transport.save(BASE/'extraction'/'status'/nonce/task/f'{rid}.json',status)
    return rid,status

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--task',default='drb2_97')
    p.add_argument('--reports',nargs='+',default=['R1','R2'])
    p.add_argument('--nonce',default='dev01')
    args=p.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,args.task,rid,args.nonce) for rid in args.reports]
        for f in concurrent.futures.as_completed(futures):
            rid,status=f.result()
            print(json.dumps({'report':rid,**status},ensure_ascii=False),flush=True)

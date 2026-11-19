"""End-to-end fake gateway tests, isolated in automatically removed temp dirs."""
import copy
import html
import io
import itertools
import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
import completeness as V
import common as C
import pipeline as P
import settings
import orchestration as O
from test_formal import rubric_fixture

class FakeGateway:
    def __init__(self,fail_graph=False):self.calls=0;self.lock=threading.Lock();self.fail_graph=fail_graph;self.orders=[]
    def open(self,req,**kwargs):
        body=json.loads(req.data);data=body['messages'][1]['content']
        with self.lock:self.calls+=1
        if data.startswith('<query>'):
            report=json.loads(html.unescape(re.search(r'<report>\s*(.*?)\s*</report>',data,re.S).group(1)))
            u=next(u for u in report['units'] if u['kind']!='heading')
            if self.fail_graph and 'REPORT_ONE_FAIL' in u['text']:raise OSError('injected graph transport failure')
            result={'report_id':'R1','branches':[{'id':'B1','question_answered':'Actual report route','claim_ids':['C1']}],
                    'claims':[{'id':'C1','statement':u['text'],'kind':'reported_input','conditions':'none stated','block_ids':[u['id']],'condition_block_ids':[],'citation_ids':[]}],'relations':[],'limitations':[]}
        else:
            data=json.loads(data)
            if 'comparison_questions' in data:
                result={'locations':[{'guide_id':g['id'],'sides':[{'report_id':r['report_id'],'claim_ids':[r['claims'][0]['id']],'read_sections':[],'focus':'original contribution'} for r in data['reports']], 'alignment_reason':'same task','coverage_limit':'supplied original regions'} for g in data['comparison_questions']]}
            elif 'report_pools' in data:
                result={'results':[{'guide_id':gp['guide']['id'],'differences':[{'id':'D1','issue':'fixture contrast','sides':[{'report_id':s['report_id'],'claim_ids':[s['local_graph']['claims'][0]['id']],'segment_ids':[s['allowed_original_ids'][0]],'contribution':'actual source passage'} for s in gp['sides']],'task_impact':'fixture impact','unresolved_dependencies':[]}],'limitations':'Only supplied material compared'} for gp in data['guide_packets']]}
            elif 'differences' in data:
                result={'bindings':[{'guide_id':d['guide_id'],'difference_id':d['id'],'report_id':s['report_id'],'reuse':[],'request':None} for d in data['differences'] for s in d['sides']]}
            elif 'rubrics' in data:
                result={'scores':[{'rubric_id':r['id'],'score':3,'reason':'Fixture: based on original','original_ids':[data['report'][0]['id']],'verification_request':None} for r in data['rubrics']]}
            elif 'guide_packets' in data:
                unpacked=C.pw.unpacked(data);rids=[r['report_id'] for r in unpacked['reports']]
                for packet in unpacked['guide_packets']:
                    if [s['report_id'] for s in packet['upstream_coverage']['localization']['sides']]!=rids:raise AssertionError('Metadata failed physical swap')
                with self.lock:self.orders.append(rids)
                result={'judgments':[{'guide_id':g['guide']['id'],'preferred_report_id':min(rids),'strength':1,'reason':'Fixture original difference','difference_ids':[d['id'] for d in g['differences']],'check_ids':[],'evidence':[{'report_id':r['report_id'],'segment_ids':[r['originals'][0]['id']]} for r in unpacked['reports']],'unresolved_dependencies':[]} for g in unpacked['guide_packets']]}
            elif 'guides' in data:
                rids=[r['report_id'] for r in data['reports']]
                with self.lock:self.orders.append(rids)
                result={'judgments':[{'guide_id':g['id'],'preferred_report_id':min(rids),'strength':1,'reason':'Fixture original prose','difference_ids':[],'check_ids':[],'evidence':[{'report_id':r['report_id'],'quote':r['text'].splitlines()[-1]} for r in data['reports']],'unresolved_dependencies':[]} for g in data['guides']]}
            else:raise AssertionError('Unknown fake request schema '+str(data.keys()))
        return io.BytesIO(json.dumps({'model':'gpt-5.5','usage':{'prompt_tokens':100,'completion_tokens':100},'choices':[{'finish_reason':'stop','message':{'content':json.dumps(result)}}]}).encode())

def prepare(root):
    suite=rubric_fixture()|{'full_query':'Fixture Query. No real evaluation.','task_key':'fixture','language':'en'}
    rp=root/'rubrics.json';O.save(rp,suite)
    route={'rubrics_sha256':V.sha(rp),'items':[{'id':r['id'],'mode':'report_only'} for r in suite['pointwise']], 'pairwise':[{'id':g['id'],'mode':'direct_original' if g['dimension'] in ('D5','D6') else 'graph_content'} for g in suite['pairwise']]}
    tp=root/'routing.json';O.save(tp,route);reports=[]
    for rid,system in settings.SYSTEMS.items():
        path=root/(rid+'.md');path.write_text('# Report\n\n'+('REPORT_ONE_FAIL' if rid=='R1' else 'Source '+rid)+' original description.\n')
        reports.append({'report_id':rid,'system':system,'path':str(path),'sha256':V.sha(path)})
    manifest={'task_key':'fixture','rubrics':str(rp),'rubrics_sha256':V.sha(rp),'routing':str(tp),'routing_sha256':V.sha(tp),'reports':reports,'budget':{'citation_units_per_report':None,'explicit_checks_per_report':None,'local_stage_workers':2},'seed_dirs':[]}
    mp=root/'manifest.json';O.save(mp,manifest);key=root/'fakekey';key.write_text('FAKE_TEST_ONLY');return mp,key

class EndToEnd(unittest.TestCase):
    def test_full_nine_system_pipeline_then_cache_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);mp,key=prepare(root);gw=FakeGateway()
            with patch.dict(os.environ,{'COMPAREDR_JUDGE_API_KEY':'FAKE_TEST_ONLY','MULTIDIM_OFFLINE':'0'}),patch('urllib.request.build_opener',return_value=gw):
                P.Runner(mp,root/'out').run();count=gw.calls
                a=V.inspect_task(V.load(mp),root/'out')
                self.assertTrue(a['framework_complete'],a['errors']);self.assertEqual(a['counts']['pw'],432);self.assertEqual(a['counts']['pairs'],36)
                self.assertIn(['R1','R2'],gw.orders);self.assertIn(['R2','R1'],gw.orders)
                P.Runner(mp,root/'out').run();self.assertEqual(gw.calls,count,'Valid cache resume caused new requests')
                # Remove only one final merged file: recreate from validated calls, no new API.
                (root/'out/pairs/R1_R2/result.json').unlink()
                self.assertFalse(V.inspect_task(V.load(mp),root/'out')['scoring_complete'])
                P.Runner(mp,root/'out').run();self.assertEqual(gw.calls,count)
                self.assertTrue(V.inspect_task(V.load(mp),root/'out')['framework_complete'])
    def test_graph_failure_does_not_block_raw_readability_or_other_pairs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);mp,key=prepare(root);gw=FakeGateway(fail_graph=True)
            with patch.dict(os.environ,{'COMPAREDR_JUDGE_API_KEY':'FAKE_TEST_ONLY','MULTIDIM_OFFLINE':'0'}),patch('urllib.request.build_opener',return_value=gw),patch('soft_contracts.time.sleep'):
                P.Runner(mp,root/'out').run()
            a=V.inspect_task(V.load(mp),root/'out');self.assertFalse(a['framework_complete']);self.assertEqual(a['counts']['graphs'],8)
            self.assertEqual(len(list((root/'out/pairs').glob('*/readability_result.json'))),36)
            self.assertEqual(a['counts']['pairs'],28)
            self.assertEqual(a['counts']['pt'],len(settings.SYSTEMS)*len(V.load(V.load(mp)['rubrics'])['pointwise']))
    def test_failed_card_can_retry_then_no_material_is_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);mp,key=prepare(root);runner=P.Runner(mp,root/'out');runner.preflight();r=runner.reports[0]
            c={'question':'fact','quote':'original','original_id':r['units'][0]['id'],'original_units':[],'citations':[],'origins':[]}
            good={'execution':'no_material','result':{'fact':{'status':'insufficient_material'}},'evidence':[]}
            with patch.object(P.A,'verify',side_effect=[RuntimeError('network'),good]) as verify:
                first=runner.verify(c,r);second=runner.verify(c,r);third=runner.verify(c,r)
            self.assertEqual(first['execution'],'failed');self.assertEqual(second['execution'],'no_material');self.assertEqual(second,third);self.assertEqual(verify.call_count,2)
    def test_PT_review_failure_is_not_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);mp,key=prepare(root);runner=P.Runner(mp,root/'out');runner.preflight();r=runner.reports[0];unit=r['segments'][0]
            rows=[{'rubric_id':g['id'],'score':3,'reason':'initial actual','original_ids':[unit['id']],'verification_request':None} for g in runner.suite['pointwise']]
            rows[0]['verification_request']={'original_id':unit['id'],'quote':unit['text'],'question':'check','search_query':'check','score_dependency':'P1'}
            def failed(c,r):return {'check_id':'K1','execution':'failed','origins':c['origins'],'evidence':[]}
            with patch.object(runner,'call',return_value={'scores':rows}),patch.object(runner,'verify',side_effect=failed):out=runner.pointwise(r)
            self.assertTrue(out['scores_complete']);self.assertFalse(out['complete']);self.assertEqual(out['final']['P1']['score'],3)
            self.assertFalse(out['final']['P1']['review_complete'])

if __name__=='__main__':unittest.main(verbosity=2)

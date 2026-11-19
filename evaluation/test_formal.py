"""Offline regressions: fake HTTP only. No evaluation labels or scores tuned."""
import copy
import hashlib
import io
import itertools
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
import orchestration as O
import settings
import completeness as V
import soft_contracts as S
import pipeline as P
import common as C
import compat
import readability_raw as RR
import repair_20260919 as Repair
import acquisition_fix as A
import retrieval_resilient as R
from scoring import aggregate
from global_limits import Limits

class Store:
    ROOT=Path('/')
    save=staticmethod(O.save)
    freeze=staticmethod(O.freeze)
    load=staticmethod(V.load)
    digest=staticmethod(C.digest)

def rubric_fixture():
    return {'pointwise':[{'id':'P'+str(i),'dimension':'D'+str(i)} for i in range(1,7)],
            'pairwise':[{'id':'G'+str(i),'dimension':'D'+str(i)} for i in range(1,7)]}

def score_fixture():
    suite=rubric_fixture();reports=[{'report_id':i,'system':s} for i,s in settings.SYSTEMS.items()]
    points={i:{'final':{r['id']:{'state':'scored','score':3,'reason':'fixture only'} for r in suite['pointwise']}} for i in settings.SYSTEMS}
    pairs=[]
    for a,b in itertools.combinations(settings.SYSTEMS,2):
        item={'pair':a+'_'+b,'report_ids':[a,b]}
        for order in ('AB','BA'):
            item[order]={'judgments':[{'guide_id':g['id'],'preferred_report_id':a if order=='AB' else b,'strength':1,'reason':'fixture only'} for g in suite['pairwise']]}
        pairs.append(item)
    return suite,reports,points,pairs

class Contracts(unittest.TestCase):
    def test_empty_graph_rejected(self):
        with self.assertRaises(S.UnusableOutput):S.fallback('graph_R1',{'claims':[]},'',{'units':[]})
    def test_missing_decision_rejected_not_tie(self):
        with self.assertRaises(S.UnusableOutput):S.fallback('pt_R1_initial',{'scores':[]},{'rubrics':[{'id':'P'}],'report':[]})
    def test_missing_navigation_rejected(self):
        d={'comparison_questions':[{'id':'G'}],'reports':[{'report_id':'R1','claims':[],'sections':[]}]}
        with self.assertRaises(S.UnusableOutput):S.fallback('loc_R1_R2_0',{},d)
    def test_section_navigation_accepted(self):
        d={'comparison_questions':[{'id':'G'}],'reports':[{'report_id':'R1','claims':[],'sections':[{'id':'S1'}]}]}
        o={'locations':[{'guide_id':'G','sides':[{'report_id':'R1','read_sections':[{'section_id':'S1','reason':'inspect actual original'}]}]}]}
        self.assertEqual(S.fallback('loc_R1_R2_0',o,d)['locations'][0]['sides'][0]['claim_ids'],[])
    def test_zero_differences_needs_explanation(self):
        d={'guide_packets':[{'guide':{'id':'G'},'sides':[]}],'report_pools':[]}
        with self.assertRaises(S.UnusableOutput):S.fallback('diff_R1_R2_0',{},d)
        o={'results':[{'guide_id':'G','differences':[],'limitations':'Reviewed original supplied regions; no substantive difference in this scope'}]}
        self.assertEqual(S.fallback('diff_R1_R2_0',o,d)['results'][0]['differences'],[])
    def test_scope_union_strict_and_soft(self):
        def side(r,c,b):return {'report_id':r,'allowed_original_ids':[b],'local_graph':{'claims':[{'id':c}]}}
        d={'guide_packets':[{'guide':{'id':'G1'},'sides':[side('R1','C1','B1'),side('R2','C1','B1')]}, {'guide':{'id':'G2'},'sides':[side('R1','C2','B2'),side('R2','C2','B2')]}],
           'report_pools':[{'report_id':r,'originals':[{'id':'B1'},{'id':'B2'}]} for r in ('R1','R2')]}
        o={'results':[{'guide_id':g,'differences':[{'id':'D','issue':'contrast','task_impact':'scope','unresolved_dependencies':[],
              'sides':[{'report_id':r,'claim_ids':['C2'],'segment_ids':['B2'],'contribution':'actual'} for r in ('R1','R2')]}],'limitations':'scope'} for g in ('G1','G2')]}
        strict=copy.deepcopy(o);compat.validate_output('diff_x',strict,d,C.loc.validate_difference)
        soft=S.fallback('diff_x',o,d)
        self.assertEqual(strict['results'][0]['differences'],soft['results'][0]['differences'])
    def test_missing_plan_rejected(self):
        with self.assertRaises(S.UnusableOutput):S.fallback('plan_x',{}, {'differences':[]})
    def test_empty_plan_after_genuine_zero_difference(self):
        self.assertEqual(S.fallback('plan_x',{'bindings':[]},{'differences':[]})['bindings'],[])
    def test_no_nfkc_or_cross_guide_shadow_quote(self):
        self.assertIsNone(Repair.span('x2','x²'));self.assertEqual(Repair.span('alpha beta','alpha\n beta'),'alpha\n beta')
        data={'reports':[{'report_id':'R1','text':'alpha'},{'report_id':'R2','text':'beta'}],'guides':[{'id':'G1'},{'id':'G2'}]}
        out={'judgments':[{'guide_id':g,'preferred_report_id':'R1','strength':1,'reason':'fixture','evidence':([{'report_id':'R1','quote':'alpha'},{'report_id':'R2','quote':'beta'}] if g=='G1' else [])} for g in ('G1','G2')]}
        Repair.readability(out,data,RR.validate)
        self.assertEqual(out['judgments'][1]['evidence'],[]);self.assertTrue(out['judgments'][1]['_quality_warnings'])
    def test_physical_swap(self):
        pair=[{'report_id':'R1','original_text':'alpha'},{'report_id':'R2','original_text':'beta'}]
        d=RR.payload('q',[{'id':'G','dimension':'D5'}],pair,'BA')
        self.assertEqual([r['report_id'] for r in d['reports']],['R2','R1'])
        o={'judgments':[{'guide_id':'G','preferred_report_id':'A','strength':1,'reason':'actual','evidence':[]}]}
        RR.validate(o,d);self.assertEqual(o['judgments'][0]['preferred_report_id'],'R2')
    def test_score_without_reason_rejected(self):
        with self.assertRaises(S.UnusableOutput):S.fallback('pt_R1_initial',{'scores':[{'rubric_id':'P','score':3}]},{'rubrics':[{'id':'P'}],'report':[]})
    def test_changed_score_no_check_warned(self):
        d={'items':[{'rubric':{'id':'P'},'initial':{'score':2},'verification':[]}]}
        r=S.fallback('pt_R1_P',{'reviews':[{'rubric_id':'P','score':3,'reason':'actual'}]},d)['reviews'][0]
        self.assertTrue(r['_quality_warnings']);self.assertEqual(r['score'],3)
    def test_unsupported_evidence_cannot_certify(self):
        o=S.fallback('K1',{'fact':{'status':'supported','evidence_ids':['made_up']}},{'evidence':[]})
        self.assertEqual(o['fact']['status'],'insufficient_material')
    def test_packed_repeated_evidence_occurrences(self):
        card={'check_id':'K1','evidence':[{'id':'E1','text':'one'},{'id':'E1','text':'two'}],'result':{'fact':{'evidence_ids':['E1']}}}
        # The legacy ID is ambiguous; packing must preserve occurrences, not delete a body.
        d={'guide_packets':[{'verification_cards':[card]}]};p=Repair.packed(d,C)
        self.assertEqual(len(p['evidence_pool']),2);self.assertEqual(C.pw.unpacked(p),d)
    def test_frozen_budgets(self):
        cfg=settings.config();self.assertEqual(settings.token_budget('graph_R1',cfg),128000);self.assertEqual(settings.token_budget('judge_R1_R2_BA',cfg),24000)
        self.assertEqual(cfg['weights'],[30,30,10,10,20])
    def test_table_and_query_boundary(self):
        text='# Title\n\nScope\n\n| Measure | Value |\n|---|---|\n| Q | 80% [s][x] |\n\n[x]: https://example.org/x\n'
        doc,units=C.prepare(text);self.assertEqual(''.join(b['text'] for b in doc['blocks']),text)
        self.assertTrue(any(u['citation_ids'] for u in units if u['kind']=='table_row'))
        data=C.graph.format_input(C.graph.payload('</query> untrusted',units))
        self.assertEqual(data.count('</query>'),1);self.assertIn('&lt;/query&gt;',data)

class Requests(unittest.TestCase):
    def test_source_body_fetch_and_pdf_parse_failure(self):
        class Connection:
            sock=None
            def request(self,*a,**kw):pass
            def getresponse(self):return self.response
            def close(self):pass
        class Response(io.BytesIO):
            status=200
            def getheader(self,key,default=''):return 'text/plain' if key=='Content-Type' else default
        import urllib.parse
        with tempfile.TemporaryDirectory() as temp:
            con=Connection();con.response=Response(b'actual scientific source body '*30)
            with patch.object(R,'BASE',Path(temp)),patch.object(R,'connection',return_value=(con,urllib.parse.urlsplit('https://example.org/source'))):
                out=R._fetch('https://example.org/source')
            self.assertEqual(out['status'],'completed',out);self.assertTrue(out['segments'])
            con.response=Response(b'%PDF fake data')
            with patch.object(R,'BASE',Path(temp)),patch.object(R,'connection',return_value=(con,urllib.parse.urlsplit('https://example.org/pdf'))),patch('subprocess.run',return_value=unittest.mock.Mock(returncode=1,stdout='')):
                out=R._fetch('https://example.org/pdf')
            self.assertEqual(out['status'],'failed');self.assertEqual(out['segments'],[]);self.assertIn('PDF parse failed',out['error'])
    def test_DNS_deadline_and_nonpublic_rejection(self):
        import socket
        ready=threading.Event()
        def blocked(*a,**k):ready.wait(.2);return []
        with patch('socket.getaddrinfo',side_effect=blocked),R.deadline_scope(.005):
            with self.assertRaises(TimeoutError):R.resolve('example.org',443)
        ready.set()
        with patch.object(R,'resolve',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]):
            with self.assertRaises(ValueError):R.connection('https://example.org/x')
    def test_authorization_halt_rejects_before_network(self):
        with tempfile.TemporaryDirectory() as temp:
            lim=Limits(Path(temp)/'limits.sqlite')
            with lim.db() as db:db.execute("insert into settings values('authorization_halt',401)")
            with self.assertRaises(RuntimeError):lim.acquire('gpt')
    def setup_call(self,p):
        Store.ROOT=p;(p/'fakekey').write_text('FAKE_TEST_KEY_NOT_A_CREDENTIAL')
        cfg=settings.config()|{'endpoint':'https://test.invalid','credential_file':'fakekey','attempts':2}
        data={'guides':[{'id':'G'}],'reports':[{'report_id':'R1','text':'a'},{'report_id':'R2','text':'b'}]}
        return cfg,data
    def test_429_exhaustion_never_success_and_resume_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);cfg,d=self.setup_call(p)
            opener=unittest.mock.Mock();opener.open.side_effect=urllib.error.HTTPError('https://test.invalid',429,'quota',{},None)
            with patch('urllib.request.build_opener',return_value=opener),patch('time.sleep'),patch.dict(os.environ,{'MULTIDIM_OFFLINE':'0','COMPAREDR_JUDGE_API_KEY':'FAKE_TEST_ONLY'}):
                for _ in range(2):
                    with self.assertRaises(S.UnusableOutput):S.invoke(p,'readability_raw_x','prompt',d,RR.validate,cfg,Store)
            self.assertEqual(opener.open.call_count,2);self.assertFalse(list(p.rglob('success.json')))
    def test_truncated_valid_json_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);cfg,d=self.setup_call(p)
            raw={'model':'gpt-5.5','choices':[{'finish_reason':'length','message':{'content':json.dumps({'judgments':[{'guide_id':'G','preferred_report_id':'R1','strength':1,'reason':'actual','evidence':[]}]})}}]}
            opener=unittest.mock.Mock();opener.open.side_effect=lambda *a,**k:io.BytesIO(json.dumps(raw).encode())
            with patch('urllib.request.build_opener',return_value=opener),patch.dict(os.environ,{'MULTIDIM_OFFLINE':'0','COMPAREDR_JUDGE_API_KEY':'FAKE_TEST_ONLY'}):
                with self.assertRaises(S.UnusableOutput):S.invoke(p,'readability_raw_x','prompt',d,RR.validate,cfg,Store)
            self.assertEqual(opener.open.call_count,2);self.assertFalse(list(p.rglob('success.json')))
    def test_cached_stage_revalidated_without_extra_request(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);cfg,d=self.setup_call(p)
            raw={'model':'gpt-5.5','usage':{'prompt_tokens':10,'completion_tokens':10},'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'judgments':[{'guide_id':'G','preferred_report_id':'R1','strength':1,'reason':'actual','evidence':[]}]})}}]}
            opener=unittest.mock.Mock();opener.open.side_effect=lambda *a,**k:io.BytesIO(json.dumps(raw).encode())
            valid=unittest.mock.Mock(side_effect=RR.validate)
            with patch('urllib.request.build_opener',return_value=opener),patch.dict(os.environ,{'MULTIDIM_OFFLINE':'0','COMPAREDR_JUDGE_API_KEY':'FAKE_TEST_ONLY'}):
                first=S.invoke(p,'readability_raw_x','prompt',d,valid,cfg,Store);second=S.invoke(p,'readability_raw_x','prompt',d,valid,cfg,Store)
            self.assertEqual(first,second);self.assertEqual(opener.open.call_count,1);self.assertEqual(valid.call_count,2)
    def test_wrong_model_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);cfg,d=self.setup_call(p)
            raw={'model':'gpt-5.6-sol','choices':[{'finish_reason':'stop','message':{'content':'{"judgments":[]}'}}]}
            opener=unittest.mock.Mock();opener.open.side_effect=lambda *a,**k:io.BytesIO(json.dumps(raw).encode())
            with patch('urllib.request.build_opener',return_value=opener),patch.dict(os.environ,{'MULTIDIM_OFFLINE':'0','COMPAREDR_JUDGE_API_KEY':'FAKE_TEST_ONLY'}):
                with self.assertRaises(S.UnusableOutput):S.invoke(p,'readability_raw_x','prompt',d,RR.validate,cfg,Store)
    def test_limits_records_requests_and_release(self):
        with tempfile.TemporaryDirectory() as temp:
            lim=Limits(Path(temp)/'limits.sqlite');key=lim.acquire('gpt',100);lim.release(key)
            with lim.db() as db:
                self.assertEqual(db.execute('select count(*) from requests').fetchone()[0],1);self.assertEqual(db.execute('select count(*) from leases').fetchone()[0],0)
    def test_backoff_does_not_change_shared_rate(self):
        with tempfile.TemporaryDirectory() as temp:
            lim=Limits(Path(temp)/'limits.sqlite',ds_rpm=300)
            for _ in range(12):lim.backoff()
            with lim.db() as db:self.assertEqual(db.execute("select value from settings where key='deepseek_rpm'").fetchone()[0],300)
    def test_gpt_429_burst_lowers_only_gpt_rate_without_releasing_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            lim=Limits(Path(temp)/'limits.sqlite',gpt_rpm=30,ds_rpm=30)
            lease=lim.acquire('gpt')
            for _ in range(2):lim.gpt_backoff()
            with lim.db() as db:self.assertEqual(db.execute("select value from settings where key='gpt_rpm'").fetchone()[0],30)
            for _ in range(4):lim.gpt_backoff()
            with lim.db() as db:
                self.assertEqual(dict(db.execute("select key,value from settings where key in ('gpt_rpm','deepseek_rpm')")),{'gpt_rpm':15,'deepseek_rpm':30})
                self.assertEqual(db.execute('select id from leases').fetchall(),[(lease,)])
                self.assertEqual(db.execute('select count(*) from rate_backoffs').fetchone()[0],1)
            lim.release(lease)
    def test_deadline_unread_not_false(self):
        with tempfile.TemporaryDirectory() as temp:
            check={'check_id':'K','question':'q','quote':'text','search_query':'q','original_units':[], 'citations':[{'url':'https://example.org/x'}]}
            with patch.object(R,'fetch',side_effect=TimeoutError('expired')),patch.object(R,'search',side_effect=TimeoutError('expired')),patch.object(C.pt.v2.old.policy,'excluded',return_value=False):
                card=A.verify(check,{'urls':[]},Path(temp),{'acquisition_seconds':180})
            self.assertEqual(card['execution'],'no_material');self.assertEqual(card['result']['fact']['status'],'insufficient_material')
            self.assertEqual(card['sources'][0]['status'],'deadline_unread')

class Aggregation(unittest.TestCase):
    def test_nine_system_sixteen_directions_and_no_agreement_gate(self):
        s,r,p,pairs=score_fixture();a=aggregate(s,r,p,pairs,[])
        self.assertEqual(a['expected_pairs'],36);self.assertEqual(a['direction_agreement']['rate'],0)
        for row in a['rows'].values():
            self.assertEqual(row['dimensions']['D3']['pairwise_received'],16);self.assertAlmostEqual(row['total'],50)
    def test_duplicate_pair_cannot_cover_missing_pair(self):
        s,r,p,pairs=score_fixture();pairs[-1]=copy.deepcopy(pairs[0])
        with self.assertRaises(ValueError):aggregate(s,r,p,pairs,[])
    def test_missing_BA_no_complete_total(self):
        s,r,p,pairs=score_fixture();del pairs[0]['BA'];a=aggregate(s,r,p,pairs,[])
        self.assertEqual(a['total_status'],'incomplete');self.assertIsNone(a['rows']['R1']['total'])
    def test_swapped_system_mapping_rejected(self):
        s,r,p,pairs=score_fixture();r[-1]['system']='DuMate'
        with self.assertRaises(ValueError):aggregate(s,r,p,pairs,[])
    def test_duplicate_guide_rejected(self):
        s,r,p,pairs=score_fixture();pairs[0]['AB']['judgments'][-1]=pairs[0]['AB']['judgments'][0]
        with self.assertRaises(ValueError):V.valid_pair(pairs[0],[g['id'] for g in s['pairwise']],['R1','R2'])
    def test_weight_normalization(self):
        s,r,p,pairs=score_fixture()
        for scores in p.values():scores['final']['P1']['score']=5
        a=aggregate(s,r,p,pairs,[]);self.assertAlmostEqual(a['rows']['R1']['total'],(75*30+50*70)/100)
    def test_missing_PT_not_reweighted(self):
        s,r,p,pairs=score_fixture();del p['R1']['final']['P1']
        with self.assertRaises(ValueError):aggregate(s,r,p,pairs,[])

if __name__=='__main__':unittest.main(verbosity=2)

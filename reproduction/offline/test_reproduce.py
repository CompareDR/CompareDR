"""Offline unit tests plus clean-directory replay and tamper detection."""
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import numpy as np
import reproduce as R
import remaining_tables as T

class ReproductionTests(unittest.TestCase):
    def test_signed_ablation_delta_and_interval_parsing(self):
        self.assertEqual(R.paper_values('tab:ablations','PT-only'),[77.50,.601,.555,-8.75])
        self.assertEqual(R.paper_values('tab:human_agreement','Hybrid framework')[-2:],[77.50,93.75])
        with mock.patch.object(R,'CHECKS',[]):
            R.paper_check('tab:ablations','PT-only',[77.50,.601,.555,-8.75],[2,3,3,2])
            with self.assertRaises(AssertionError):
                R.paper_check('tab:ablations','PT-only',[77.50,.601,.555,8.75],[2,3,3,2])

    def test_fit_postconditions_are_explicit(self):
        rows=np.array([[0,0,1,2]])
        for result,message in (({'success':False},'converge'),
            ({'success':True,'theta':np.ones((40,9)),'tau':np.array([-1,0,1])},'centered'),
            ({'success':True,'theta':np.full((40,9),np.nan),'tau':np.array([-1,0,1])},'non-finite')):
            with self.subTest(message=message),mock.patch.object(R.O,'fit',return_value=result):
                with self.assertRaisesRegex(ValueError,message):R.checked_fit(rows,9)
        self.assertIsNone(R.checked_fit(np.empty((0,4),dtype=int),9))

    def test_unsuccessful_optimizer_is_rejected_in_all_execution_modes(self):
        for options,extra in (([],{}),(['-O'],{}),([] ,{'PYTHONOPTIMIZE':'1'})):
            with self.subTest(options=options,extra=extra),tempfile.TemporaryDirectory() as temp:
                output=Path(temp)/'failed-run'
                code="""import sys
import reproduce as r
original=r.O.minimize
def unsuccessful(*args,**kwargs):
    result=original(*args,**kwargs)
    result.success=False
    result.message='Injected unsuccessful optimizer termination'
    return result
r.O.minimize=unsuccessful
sys.argv=['reproduce','--output',sys.argv[1]]
r.main()
"""
                result=subprocess.run([sys.executable,'-B',*options,'-c',code,str(output)],cwd=R.ROOT,
                    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**extra},capture_output=True,text=True,timeout=90)
                self.assertNotEqual(result.returncode,0,result.stdout)
                audit=json.loads((output/'AUDIT.json').read_text(encoding='utf-8'))
                self.assertEqual(audit['status'],'failed')
                self.assertEqual(audit['numerically_reproduced_tables'],0)
                self.assertFalse(audit['main_refit_performed'])

    def test_failure_audits_survive_partial_tables_and_nonfinite_details(self):
        for value in (float('nan'),float('inf'),float('-inf')):
            with self.subTest(value=value),tempfile.TemporaryDirectory() as temp:
                output=Path(temp)/'output'
                def fail():
                    R.check('tab:benchmark_resources:first row',True)
                    R.check('tab:benchmark_resources:second row',False,{'value':value})
                with mock.patch.object(R,'CHECKS',[]),mock.patch.object(R,'RESULTS',{}),mock.patch.object(R,'verify_inputs',side_effect=fail),mock.patch.object(sys,'argv',['reproduce','--output',str(output)]),contextlib.redirect_stderr(io.StringIO()),contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:R.main()
                self.assertEqual(error.exception.code,1)
                audit=json.loads((output/'AUDIT.json').read_text(encoding='utf-8'))
                self.assertEqual(audit['status'],'failed');self.assertEqual(audit['numerically_reproduced_tables'],0)
                self.assertEqual(audit['table_statuses'],{})
                self.assertIn('nonfinite',audit['checks'][-1]['detail']['value'])

    def test_utf8_inputs_under_ascii_locale(self):
        env={**os.environ,'LC_ALL':'C','PYTHONCOERCECLOCALE':'0','PYTHONUTF8':'0','PYTHONDONTWRITEBYTECODE':'1'}
        # Avoid unrelated site .pth files: test package decoding, not host startup.
        paths=[str(Path(m.__file__).resolve().parent.parent) for m in (np,R.scipy)]
        code="import sys; sys.path.extend("+json.dumps(paths)+"); import reproduce as r; r.verify_inputs(); r.benchmark(); print('PASS')"
        result=subprocess.run([sys.executable,'-B','-S','-c',code],cwd=R.ROOT,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_main_generation_identity_and_ranking(self):
        b=R.read('data/benchmark.json')
        self.assertEqual(b['systems']['R1'][0],'GPT-6')
        self.assertEqual(b['systems']['R4'][1],'LongCat-DeepResearch')
        scores=R.read('data/expected_main.json')
        self.assertEqual([r['report_id'] for r in scores['table'][:3]],['R1','R4','R5'])
        self.assertEqual(len({(r['query'],r['report_id']) for r in b['report_manifest']}),360)

    def test_current_inventory_transposition_and_manifest_counts(self):
        R.benchmark()
        self.assertEqual(R.paper_values('tab:benchmark_resources','Collected reports'),[54,198,108,360])
        self.assertEqual(R.paper_values('tab:benchmark_resources','Human-annotated report pairs'),[12,44,24,80])

    def test_rubric_description_column_is_not_a_numeric_input(self):
        self.assertEqual(R.paper_values('tab:rubric_distribution','Evidence',skip=2),[106,38,144])
        self.assertEqual(R.paper_values('tab:rubric_distribution','Total',skip=2),[776,323,1099])

    def test_network_disabled(self):
        with self.assertRaisesRegex(RuntimeError,'offline-only'):
            socket.create_connection(('example.invalid',443))

    def test_perfect_metrics(self):
        m=R.metric(['A','B','tie'],['A','B','tie'])
        self.assertEqual((m['accuracy'],m['kappa'],m['macro_f1']),(1,1,1))

    def test_absent_class_f1_not_silently_removed(self):
        self.assertAlmostEqual(R.metric(['A','B'],['A','B'])['macro_f1'],2/3)

    def test_pairwise_symmetry_and_probability(self):
        tau=np.array([-1.4,-.35,.35,1.4]);x=np.array([-10.,-1.,0.,1.,10.])
        self.assertTrue(np.allclose(R.O.probs(x,tau).sum(-1),1))
        self.assertTrue(np.allclose(R.O.expect(x,tau),-R.O.expect(-x,tau)))

    def test_missing_channel_is_not_zero(self):
        pt=np.array([[[100,np.nan,np.nan,np.nan,np.nan,np.nan]]])
        pw=np.array([[[np.nan,80,60,40,20,40]]])
        s=R.combine(pt,pw)[0,0]
        self.assertTrue(np.allclose(s,[100,80,60,40,30,70]))

    def test_bootstrap_deterministic_and_clusters(self):
        rows=[{'task':f'drb1_{q}'} for q in range(4) for _ in range(2)]
        vals=[0,0,1,1,0,0,1,1]
        self.assertTrue(np.array_equal(R.bootstrap(rows,vals),R.bootstrap(rows,vals)))

    def test_icc_identity(self):
        self.assertAlmostEqual(R.icc([1,4,6],[1,4,6]),1.)

    def test_physical_swap_uses_restored_identity(self):
        rows=[]
        for a,b,s in [('R1','R2',1),('R1','R3',-1),('R2','R3',1)]:
            for order in ('AB','BA'):rows.append(['q',a,b,'g',order,s])
        v=R.stability(rows,['R1','R2','R3'])
        self.assertEqual(v['direction_agree'],3)
        self.assertEqual(v['strict_reversal'],0)
        self.assertEqual(v['cycles'],1)

    def test_expected_main_counts(self):
        d=R.read('data/main_judgments.json')
        self.assertEqual((len(d['queries']),len(d['systems']),len(d['pointwise']),len(d['pairwise'])),(40,9,6984,23256))

    def test_threshold_boundary_is_inclusive_tie(self):
        self.assertEqual(T.predict([-2,-1,0,1,2],1),['degrade','equivalent','equivalent','equivalent','improve'])

    def test_percentage_negative_base_and_zero_guard(self):
        self.assertEqual(T.percentage(2,-20),10.)
        with self.assertRaises(ValueError):T.percentage(1,0)

    def test_threshold_tiebreak_chooses_smallest_boundary(self):
        result=T.optimize([-2,0,2],['degrade','equivalent','improve'],'macro_f1',R.metric)
        self.assertEqual(result['threshold_boundary'],0.)
        self.assertEqual(result['metrics']['macro_f1'],1.)
        self.assertEqual(result['regime_upper_exclusive'],2.)

    def test_duplicate_candidate_identity_rejected(self):
        with self.assertRaises(ValueError):T.assert_unique([{'id':'a'},{'id':'a'}],lambda r:r['id'])

    def test_equivalent_targets_deduplicated_without_scores(self):
        m=R.read('data/controlled_selected_packet.json')
        dual={c['case_id'] for c in m['cases'] if len(T.targets(c,'equivalent'))==2}
        self.assertEqual(dual,{'P032','P043','P045'})
        self.assertEqual(sum(len(T.targets(c,k)) for c in m['cases'] for k in T.LABELS),123)

    def test_source_missing_does_not_drop_dimension_case(self):
        groups=T.reconstruct_groups(R.read('data/controlled_native_scores.json'),R.read('data/controlled_selected_packet.json'))
        self.assertEqual({n:len(v) for n,v in groups.items()},
            {'Full framework':120,'Same-coverage PT':120,'RACE':120,'Source protocols':119})
        self.assertIn(('P049','equivalent'),{(r['case_id'],r['construction_direction']) for r in groups['Full framework']})

    def test_selected_labels_have_exact_report_bindings(self):
        a=R.read('data/controlled_selected_packet.json')
        self.assertEqual(a['label_type'],'author_confirmed_matched_version')
        self.assertEqual(len(a['labels']),120)
        self.assertTrue(all(len(r['revision_sha256'])==64 and len(r['base_sha256'])==64 for r in a['labels']))
        self.assertIn('data/controlled_selected_packet.json',R.read('INPUT_HASHES.selected.json'))

    def test_metadata_join_has_exact_query_ids(self):
        d=R.read('data/query_characteristics.json')
        self.assertEqual({r['query_id'] for r in d['rows']},set(R.read('data/benchmark.json')['queries']))
        self.assertEqual(len(d['rows']),40)

    def test_clean_directory_replay_and_tamper_detection(self):
        # Copies only offline/, not the private source audit or original runs.
        with tempfile.TemporaryDirectory(prefix='comparedr-offline-test-') as temp:
            root=Path(temp); package=root/'renamed-package'
            shutil.copytree(R.ROOT,package,ignore=shutil.ignore_patterns('__pycache__'))
            env={**os.environ,'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1'}
            command=[sys.executable,str(package/'reproduce.py'),'--output',str(root/'results')]
            result=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            a=json.loads((root/'results/AUDIT.json').read_text())
            self.assertTrue(a['main_refit_performed']);self.assertEqual(a['failed_checks'],0)
            self.assertEqual((a['numerically_reproduced_tables'],a['archival_provenance_tables'],a['author_attested_label_tables']),(16,13,3))
            self.assertTrue(a['author_confirmation_accepted'])
            self.assertFalse(a['all_paper_tables_fully_verified'])
            changed=package/'data/main_judgments.json'
            changed.write_text(changed.read_text()+'\n')
            command[-1]=str(root/'tamper-results')
            result=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True,timeout=60)
            self.assertNotEqual(result.returncode,0)
            a=json.loads((root/'tamper-results/AUDIT.json').read_text())
            self.assertEqual(a['status'],'failed');self.assertEqual(a['failed_checks'],1)
            self.assertIn('sha256:data/main_judgments.json',a['error'])

if __name__=='__main__':unittest.main(verbosity=2)

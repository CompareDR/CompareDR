"""Offline intake tests. Synthetic reports exist only inside temporary folders."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from validate import HERE, QUERYSET_SHA256, load, validate
from build_template import build


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copy2(HERE/'queries.json', self.root/'queries.json')
        (self.root/'reports').mkdir()
        self.data = load(HERE/'submission.template.json')
        self.data['system'] = dict(name='Synthetic fixture', model='Fixture model', harness='Fixture harness',
            reasoning='undisclosed', generation_start='2026-11-17', generation_end='2026-11-17', settings={'purpose':'format test only'})
        self.data['permission_to_evaluate'] = True
        self.data['redistribution_notes'] = 'Synthetic test data only'
        for row in self.data['reports']:
            text = '# Synthetic format fixture\n\nThis is not an evaluated report. https://example.com/source\n'
            (self.root/row['report_path']).write_text(text)
            row['sha256'] = hashlib.sha256(text.encode()).hexdigest()
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        (self.root/'submission.json').write_text(json.dumps(self.data))

    def test_valid_package_is_read_only(self):
        before = (self.root/'submission.json').read_bytes()
        result = validate(self.root)
        self.assertEqual(result['status'],'format_valid')
        self.assertEqual(result['completed_reports'],40)
        self.assertEqual((self.root/'submission.json').read_bytes(),before)

    def test_missing_report_rejected(self):
        (self.root/self.data['reports'][0]['report_path']).unlink()
        with self.assertRaisesRegex(ValueError,'missing or unsafe'):validate(self.root)

    def test_hash_repair_changes_only_hashes(self):
        old = copy.deepcopy(self.data)
        row = self.data['reports'][0]
        (self.root/row['report_path']).write_text('Changed synthetic fixture')
        with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):validate(self.root)
        validate(self.root,fill_hashes=True)
        new = load(self.root/'submission.json')
        self.assertNotEqual(new['reports'][0]['sha256'],old['reports'][0]['sha256'])
        old['reports'][0]['sha256']=new['reports'][0]['sha256']
        self.assertEqual(new,old)

    def test_duplicate_unknown_or_missing_ids_rejected(self):
        for change in ('duplicate','unknown','missing'):
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                if change=='duplicate':data['reports'][1]['query_id']=data['reports'][0]['query_id']
                elif change=='unknown':data['reports'][0]['query_id']='not-a-frozen-query'
                else:data['reports'].pop()
                (self.root/'submission.json').write_text(json.dumps(data))
                with self.assertRaises(ValueError):validate(self.root)

    def test_unsafe_paths_and_symlinks_rejected(self):
        self.data['reports'][0]['report_path']='../outside.md';self.save()
        with self.assertRaisesRegex(ValueError,'use reports/'):validate(self.root)
        self.data['reports'][0]['report_path']='reports/'+self.data['reports'][0]['query_id']+'.md';self.save()
        (self.root/'unrelated-link').symlink_to(self.root/'queries.json')
        with self.assertRaisesRegex(ValueError,'Symlinks'):validate(self.root)

    def test_failed_tasks_are_not_complete(self):
        row = self.data['reports'][0]
        (self.root/row['report_path']).unlink()
        row.update(status='failed',report_path=None,sha256=None,error='Generation failed')
        self.save()
        result=validate(self.root)
        self.assertEqual(result['status'],'incomplete')
        self.assertEqual(result['completed_reports'],39)
        self.assertFalse(result['ready_for_maintainer_review'])
        command=subprocess.run([sys.executable,str(HERE/'validate.py'),str(self.root)],capture_output=True,text=True)
        self.assertEqual(command.returncode,2)

    def test_original_queries_are_pinned(self):
        self.assertEqual(hashlib.sha256((HERE/'queries.json').read_bytes()).hexdigest(),QUERYSET_SHA256)
        (self.root/'queries.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'Query set differs'):validate(self.root)

    def test_permissions_metadata_and_empty_text_rejected(self):
        for field in ('permission','settings','dates','empty'):
            with self.subTest(field=field):
                data=copy.deepcopy(self.data)
                if field=='permission':data['permission_to_evaluate']=False
                elif field=='settings':data['system']['settings']={}
                elif field=='dates':data['system']['generation_end']='2026-11-16'
                else:(self.root/data['reports'][0]['report_path']).write_text('')
                (self.root/'submission.json').write_text(json.dumps(data))
                with self.assertRaises(ValueError):validate(self.root)

    def test_zip_is_deterministic_and_contains_no_answers(self):
        first=build();second=build()
        self.assertEqual(first,second)
        with zipfile.ZipFile(HERE.parent/'website/dist/submission-template.zip') as archive:
            names=set(archive.namelist())
            self.assertTrue({'submission/'+s for s in ('QUERY_ATTRIBUTION.md','LICENSE',
                'licenses/DRB-I-LICENSE.txt','licenses/DRB-II-DATA-LICENSE.txt',
                'licenses/CC-BY-4.0.txt','licenses/ResearchRubrics-MIT-LICENSE.txt',
                'licenses/QUERY_LICENSE_MATRIX.md','licenses/DRB2_ARTICLE_ATTRIBUTIONS.md')} <= names)
            self.assertFalse(any('rubric' in n.lower() and not n.endswith('MIT-LICENSE.txt') or
                                 'criterion' in n.lower() for n in names))
            queries=json.loads(archive.read('submission/queries.json'))['queries']
            matrix=archive.read('submission/licenses/QUERY_LICENSE_MATRIX.md').decode()
            for q in queries:
                self.assertIn('| '+q['query_id']+' |',matrix)
            self.assertEqual(len(queries),40)
            self.assertTrue(all(set(q)=={'query_id','language','query'} for q in queries))
            archive.extractall(self.root/'unpacked')
        base=self.root/'unpacked/submission'
        result=subprocess.run([sys.executable,str(base/'validate.py'),str(base)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1) # The unfilled template must never pass.
        self.assertIn('permission_to_evaluate',result.stdout)


if __name__=='__main__':
    unittest.main()

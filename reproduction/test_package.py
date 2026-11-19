"""Distribution-layer tests; no credentials, downloads or original workspace needed."""
import unittest
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest import mock
import sanitize_links as S
import verify_materials as V
import verify_package as P

class DistributionTests(unittest.TestCase):
    def test_integrity_survives_optimized_python(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for filename in ('verify_package.py','verify_materials.py'):shutil.copy2(P.ROOT/filename,root/filename)
            (root/'payload.txt').write_text('fixture',encoding='utf-8')
            files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
            files['payload.txt']='0'*64
            (root/'PACKAGE_HASHES.json').write_text(json.dumps(files),encoding='utf-8')
            for flags,extra in (([],{}),(['-O'],{}),([],{"PYTHONOPTIMIZE":"1"})):
                with self.subTest(flags=flags,environment=extra):
                    env={**os.environ,**extra,'PYTHONDONTWRITEBYTECODE':'1'}
                    result=subprocess.run([sys.executable,'-B',*flags,str(root/'verify_package.py')],capture_output=True,text=True,env=env)
                    self.assertNotEqual(result.returncode,0);self.assertIn('Checksum mismatch',result.stderr)
                    code="import verify_materials as v; v.read=lambda p: {'selected_labels':'x','files':[]} if p=='materials/MANIFEST.json' else {'cases':[],'labels':[]}; v.verify()"
                    result=subprocess.run([sys.executable,'-B',*flags,'-c',code],cwd=root,capture_output=True,text=True,env=env)
                    self.assertNotEqual(result.returncode,0);self.assertIn('Material integrity check failed',result.stderr)

    def test_extra_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'PACKAGE_HASHES.json').write_text('{}',encoding='utf-8')
            for target in (root/'absent',root):
                link=root/'extra-link';link.symlink_to(target,target_is_directory=target==root)
                with mock.patch.object(P,'ROOT',root),self.assertRaisesRegex(ValueError,'symlink'):
                    P.main()
                link.unlink()

    def test_materials_under_ascii_locale(self):
        env={**os.environ,'LC_ALL':'C','PYTHONCOERCECLOCALE':'0','PYTHONUTF8':'0','PYTHONDONTWRITEBYTECODE':'1'}
        result=subprocess.run([sys.executable,'-B','-S',str(P.ROOT/'verify_materials.py')],capture_output=True,text=True,env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'passed')

    def test_tracking_removed_without_changing_article(self):
        cleaned,counts=S.clean_text('[source](https://example.org/article?id=12&utm_source=search&srsltid=tracking#sec)')
        self.assertEqual(cleaned,'[source](https://example.org/article?id=12#sec)')
        self.assertEqual(counts,{'utm_source':1,'srsltid':1})

    def test_public_document_identifier_retained(self):
        text='https://example.org/document?enc=public-document-identifier&key=term'
        self.assertEqual(S.clean_text(text),(text,{}))

    def test_normalization_is_idempotent(self):
        once,_=S.clean_text('https://example.org/page?utm_source=search')
        self.assertEqual(S.clean_text(once),(once,{}))

    def test_all_material_identities_and_paper_procedure(self):
        result=V.verify()
        self.assertEqual((result['bases'],result['revisions'],result['target_dimension_judgments']),(40,120,123))
        self.assertTrue(result['paper_procedure_matches'])

if __name__=='__main__':unittest.main(verbosity=2)

"""Offline CompareDR website regressions; do not invoke experiments or APIs."""
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from sync_comparedr import make_data, table, leaderboard_rows, leaderboard_markdown, leaderboard_table, project_context

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
INPUT = ROOT / 'manuscript'
BACKUP = ROOT / 'baseline'
SCORES = ('D1', 'D2', 'D3', 'D4', 'D5_D6', 'overall')


class PublicWebsiteTests(unittest.TestCase):
    def test_leaderboard_identifier_contrast(self):
        foreground=re.search(r'<style>\.leaderboard \.harness,\.leaderboard td:nth-child\(1\)\{color:(#[a-f0-9]{6})\}</style>',self.html)[1]
        css=(DIST/'assets/style.css').read_text(encoding='utf-8')
        hover=re.search(r'\.leaderboard tbody tr:hover\{background:(#[a-f0-9]{6})\}',css)[1]
        def luminance(color):
            values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
            linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
            return sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))
        for background in ('#ffffff',hover):
            light,dark=sorted((luminance(foreground),luminance(background)),reverse=True)
            self.assertGreaterEqual((light+.05)/(dark+.05),4.5)

    def test_clean_build_without_existing_dist(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'website'
            root.mkdir()
            shutil.copytree(ROOT.parent/'submissions',root.parent/'submissions')
            shutil.copytree(ROOT.parent/'data/evaluation/main9/rubrics',root.parent/'data/evaluation/main9/rubrics')
            for directory in ('docs','evaluation','experiments','reproduction','data/reports','data/annotations'):
                shutil.copytree(ROOT.parent/directory,root.parent/directory,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(ROOT.parent/'README.md',root.parent/'README.md')
            for name in ('manuscript','baseline','templates'):
                shutil.copytree(ROOT/name,root/name)
            shutil.copy2(ROOT/'sync_comparedr.py',root/'sync_comparedr.py')
            shutil.copy2(ROOT/'participation.md',root/'participation.md')
            shutil.copy2(ROOT/'site_metadata.json',root/'site_metadata.json')
            result=subprocess.run([sys.executable,'-B','sync_comparedr.py'],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            expected={str(p.relative_to(DIST)):p.read_bytes() for p in DIST.rglob('*') if p.is_file()}
            actual={str(p.relative_to(root/'dist')):p.read_bytes() for p in (root/'dist').rglob('*') if p.is_file()}
            self.assertEqual(actual,expected)
            self.assertEqual((root.parent/'LEADERBOARD.md').read_bytes(),(ROOT.parent/'LEADERBOARD.md').read_bytes())
            self.assertEqual((root.parent/'README.md').read_bytes(),(ROOT.parent/'README.md').read_bytes())

    def test_static_boards_are_identical_without_javascript(self):
        for name in ('index.html','leaderboard.html'):
            text=(DIST/name).read_text()
            rows=text.split('<tbody id="board">',1)[1].split('</tbody>',1)[0]
            self.assertEqual(rows,leaderboard_rows(self.data))
            self.assertEqual(rows.count('<tr>'),9)
            self.assertNotIn('{{',text)
            self.assertIn('Rank always denotes overall rank',text)

    def test_repository_leaderboard_is_generated(self):
        text=(ROOT.parent/'LEADERBOARD.md').read_text()
        self.assertEqual(text,leaderboard_markdown(self.data))
        self.assertEqual(len(re.findall(r'^\| [1-9] \|',text,re.M)),9)
        self.assertIn('**83.08**',text)
        self.assertIn('**93.59**',text)
        self.assertIn('**74.52**',text)
        readme=(ROOT.parent/'README.md').read_text()
        summary=readme.split('<!-- LEADERBOARD_SUMMARY_START -->',1)[1].split('<!-- LEADERBOARD_SUMMARY_END -->',1)[0].strip()
        self.assertEqual(summary,leaderboard_table(self.data))

    def test_readme_and_reference_have_all_six_score_columns(self):
        expected_header=['Rank','Research harness','Model','Responsiveness','Evidence','Reasoning','Synthesis','Readability','Overall']
        parsed=[]
        for name in ('README.md','LEADERBOARD.md'):
            lines=(ROOT.parent/name).read_text().splitlines()
            header=next(i for i,line in enumerate(lines) if line.startswith('| Rank |'))
            cells=lambda line:[s.strip() for s in line.strip('|').split('|')]
            self.assertEqual(cells(lines[header]),expected_header)
            rows=[cells(line) for line in lines[header+2:header+11]]
            self.assertEqual(len(rows),9)
            for row,source in zip(rows,self.data['leaderboard']):
                self.assertEqual(len(row),9)
                self.assertEqual(row[:3],[str(source['rank']),source['harness'],source['model']])
                self.assertEqual([s.replace('**','') for s in row[3:]],[f'{source[k]:.2f}' for k in SCORES])
            parsed.append(rows)
        self.assertEqual(parsed[0],parsed[1])

    def test_every_display_surface_exposes_five_dimensions_and_total(self):
        class Board(HTMLParser):
            def __init__(self):
                super().__init__();self.inside=False;self.rows=[];self.current=[];self.cell=None
            def handle_starttag(self,tag,attrs):
                if tag=='tbody' and dict(attrs).get('id')=='board':self.inside=True
                if self.inside and tag=='tr':self.current=[]
                if self.inside and tag=='td':self.cell=''
            def handle_data(self,data):
                if self.cell is not None:self.cell+=data
            def handle_endtag(self,tag):
                if self.inside and tag=='td':self.current.append(self.cell);self.cell=None
                if self.inside and tag=='tr':self.rows.append(self.current)
                if self.inside and tag=='tbody':self.inside=False
        for name in ('index.html','leaderboard.html'):
            parser=Board();parser.feed((DIST/name).read_text())
            self.assertEqual(len(parser.rows),9)
            for row,source in zip(parser.rows,self.data['leaderboard']):
                self.assertEqual(len(row),8)
                self.assertEqual(row[2:],[f'{source[k]:.2f}' for k in SCORES])

    def test_machine_readable_leaderboard(self):
        board=json.loads((DIST/'leaderboard.json').read_text())
        self.assertEqual(board['rows'],self.data['leaderboard'])
        self.assertEqual(board['weights'],self.data['weights'])
        self.assertEqual(board['protocol'],self.data['leaderboard_protocol'])
        self.assertEqual((board['systems'],board['queries'],board['reports'],board['within_query_pairs']),(9,40,360,1440))
        self.assertEqual(board['snapshot_date'],'2026-11-16')

    def test_participation_is_not_an_implemented_upload_service(self):
        guide=(DIST/'participation.md').read_text()
        self.assertEqual(guide,(ROOT/'participation.md').read_text())
        self.assertIn('not** a generic',guide)
        self.assertIn('maintainer integration',guide)
        self.assertIn('not automatic judging',guide)
        self.assertTrue((ROOT.parent/'data/evaluation/main9').is_dir())
        text=(DIST/'leaderboard.html').read_text()
        self.assertNotIn('<form',text)
        self.assertIn('https://github.com/CompareDR/CompareDR/issues/new?template=submit-system.yml',text)
        self.assertIn('submission-template.zip',text)
        self.assertTrue((DIST/'submission-template.zip').is_file())
        self.assertIn('submission-format.md',text)
        self.assertIn('still requires maintainer integration',text)

    def test_javascript_interactions(self):
        node=os.environ.get('NODE_BINARY') or shutil.which('node')
        if not node:self.skipTest('Node is required only for interaction unit tests.')
        result=subprocess.run([node,str(ROOT/'test_interactions.cjs')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_visible_validation_scope(self):
        section=self.html.split('<section id="experiments"',1)[1].split('</section>',1)[0]
        self.assertIn('nine systems',section)
        self.assertIn('80 annotated pairs from a fixed seven-system collection',section)

    def test_main_generation_identity(self):
        rows=self.data['leaderboard']
        self.assertEqual([r['model'] for r in rows[:3]],['GPT-6','LongCat','Kimi K3'])
        self.assertEqual(rows[0]['harness'],'ChatGPT Deep Research')
        self.assertEqual([round(r['overall'],2) for r in rows[:3]],[83.08,82.62,78.86])
        self.assertNotIn('v2',json.dumps(rows))
        cards = self.html.split('<div class="findings">', 1)[1].split('</div>', 1)[0]
        self.assertEqual(re.findall(r'<strong>(.*?)</strong>', cards), ['83.08','82.64 / 78.79','74.52'])
        self.assertIn('ChatGPT Deep Research leads overall', cards)
        self.assertNotIn('LongCat-DeepResearch leads overall', cards)
        self.assertEqual(max(rows,key=lambda r:r['D5_D6'])['model'],'Kimi K3')

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((DIST / 'data.json').read_text())
        cls.html = (DIST / 'index.html').read_text()
        cls.baseline = json.loads((INPUT / 'baseline_data.json').read_text())

    def test_manuscript_snapshot_integrity(self):
        manifest = json.loads((INPUT / 'source/PAPER_MANIFEST.json').read_text())
        for key in ('main.tex', 'iclr2027_conference.bib'):
            self.assertEqual(hashlib.sha256((INPUT / 'source' / key).read_bytes()).hexdigest(), manifest['files']['source/'+key])
        self.assertEqual(self.data, make_data())

    def test_latest_title(self):
        self.assertEqual(self.data['title'], 'CompareDR: Benchmarking Deep Research Reports from Individual Quality to Comparative Merit')
        self.assertIn('<title>'+self.data['title']+'</title>', self.html)
        self.assertIn('CompareDR: Benchmarking', self.html)
        self.assertNotIn('{{', self.html)

    def test_leaderboard_full_precision_and_paper_labels(self):
        original = json.loads((INPUT / 'leaderboard_full_precision.json').read_text())
        self.assertEqual(len(self.data['leaderboard']), 9)
        self.assertEqual(self.data['score_scale'], [0, 100])
        for row, source, manuscript in zip(self.data['leaderboard'], original['table'], table('tab:system_results')):
            self.assertEqual(row['model'], '—' if manuscript[0]=='---' else manuscript[0])
            self.assertEqual(row['harness'], manuscript[1])
            for key, printed in zip(SCORES, manuscript[2:]):
                self.assertEqual(row[key], source[key])
                self.assertEqual(f'{row[key]:.2f}', f'{float(printed):.2f}')
            total = sum(row[k]*v for k,v in self.data['weights'].items())/100
            self.assertAlmostEqual(total, row['overall'])

    def test_all_exports_agree(self):
        embedded = (DIST / 'assets/data.js').read_text().removeprefix('window.BENCH_DATA = ').strip().removesuffix(';')
        self.assertEqual(json.loads(embedded), self.data)
        with (DIST / 'leaderboard.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 9)
        for row, exported in zip(self.data['leaderboard'], rows):
            for key in ('model','harness'):
                self.assertEqual(row[key], exported[key])
            for key in SCORES:
                self.assertEqual(row[key], float(exported[key]))
        experiments = json.loads((DIST / 'experiment_results.json').read_text())
        for key, value in experiments.items():
            self.assertEqual(value, self.data[key])

    def test_frozen_inputs_and_style_are_unchanged(self):
        for key in ('queries','domains','stats','weights','download_scope'):
            self.assertEqual(self.data[key], self.baseline[key])
        for path in ('assets/style.css','assets/table2_domain_distribution.svg'):
            self.assertEqual((DIST / path).read_bytes(), (BACKUP / path).read_bytes())
        self.assertEqual(len(self.data['queries']),40)
        self.assertEqual(sum(q['pt_count']+q['pw_count'] for q in self.data['queries']),1099)

    def test_primary_and_component_judge_remain_gpt55(self):
        self.assertEqual(self.data['leaderboard_protocol']['judge'],'GPT-5.5')
        self.assertEqual(self.data['leaderboard_protocol']['verifier'],'deepseek-v4.1-flash')
        self.assertEqual(self.data['model_settings']['component_judge'],'GPT-5.5')
        self.assertEqual([r['agreement'] for r in self.data['ablations']],[86.25,77.50,82.50,86.25,83.75])
        self.assertEqual([r['delta'] for r in self.data['ablations']],[None,-8.75,-3.75,0.,-2.50])

    def test_controlled_comparison_is_common_human_confirmed_set(self):
        study = self.data['controlled_revisions']
        self.assertEqual((study['constructed'],study['evaluated'],study['excluded']),(120,119,1))
        self.assertEqual([r['method'] for r in study['rows']],['Full framework','Same-coverage PT','RACE','Source protocols'])
        self.assertEqual([r['macro_f1'] for r in study['rows']],[64.2,37.8,40.8,34.1])
        for row in study['rows']:
            self.assertEqual(sum(row[key]['total'] for key in ('improvement','degradation','equivalent')),119)
            correct = sum(row[key]['correct'] for key in ('improvement','degradation','equivalent'))
            self.assertEqual(round(100*correct/119,1),row['accuracy'])
        self.assertEqual(self.data['controlled_dimensions'][-1]['n'],123)
        self.assertIn('within-set calibration', self.html)

    def test_cross_judge_uses_current_deepseek_and_gpt_reference(self):
        primary, deepseek, gemini = self.data['cross_judge']
        self.assertEqual(primary['judge'],'GPT-5.5')
        self.assertIsNone(primary['rho'])
        self.assertEqual((deepseek['judge'],deepseek['order_agreement'],deepseek['reversals'],deepseek['icc'],deepseek['bias']),('DeepSeek-v4.1f',86.09,13.02,.950,.065))
        self.assertEqual(gemini['rho'],.4)
        self.assertEqual(self.data['judge_pilot'][0]['values'],['300/300','290/300','298/300'])

    def test_entry_and_usage_match_paper(self):
        row = self.data['new_system_entry'][1]
        self.assertEqual((row['new_pairs'],row['token_savings'],row['mae']),(80,64.23,.318))
        self.assertEqual(self.data['token_usage'][-1]['total_m'],688.47)

    def test_no_stale_claims_or_private_paths_in_public_artifacts(self):
        for path in DIST.rglob('*'):
            if not path.is_file():
                continue
            if path.suffix == '.zip':
                with zipfile.ZipFile(path) as archive:
                    text='\n'.join(archive.read(name).decode('utf-8') for name in archive.namelist())
            elif path.suffix in ('.png', '.pdf'):
                # Original paper figures are checked byte-for-byte separately.
                continue
            else:
                text = path.read_text()
            for forbidden in ('DeepSeek-v4-flash','agent-consensus silver','Across 32 queries','96 revisions','14 remain unresolved','/'+'Users'+'/','/'+'Volumes'+'/','Bearer '):
                self.assertFalse(forbidden in text, f'{path}: unexpected {forbidden}')
            self.assertFalse(re.search(r'[Dd]eep[Ss]eek[^"\s<]{0,30}1017',text),str(path))
        self.assertIn('not all 1,099 criteria',self.html)

    def test_paper_figure_is_exact_not_redrawn(self):
        for name in ('framework.png','framework.pdf'):
            self.assertEqual((DIST/'assets'/name).read_bytes(),(ROOT.parent/'docs/assets'/name).read_bytes())
        self.assertIn('assets/framework.png',self.html)
        self.assertIn('assets/framework.pdf',self.html)
        self.assertNotIn('class="workflow"',self.html)

    def test_authors_and_manuscript_citation(self):
        meta=json.loads((ROOT/'site_metadata.json').read_text())
        names=[a['name'] for a in meta['authors']]
        self.assertEqual(names,['Wanli Wu','He Zhu','Yue Xu','Haolin Ren','Yan Chen','XunLiang Cai','Fan Yang','LingChuan Liu','Shizhu He'])
        self.assertEqual([a['name'] for a in meta['authors'] if a.get('equal')],names[:3])
        self.assertEqual([a['name'] for a in meta['authors'] if a.get('corresponding')],names[-2:])
        context,bibtex=project_context(self.data['title'])
        self.assertEqual((DIST/'comparedr.bib').read_text(),bibtex)
        self.assertIn(context['AUTHORS'],self.html)
        self.assertIn('author = {'+' and '.join(names)+'}',bibtex)
        self.assertIn('@unpublished',bibtex)
        self.assertNotIn('arxiv.org/abs/',bibtex)
        self.assertEqual(self.html.count('aria-disabled="true"'),2)

    def test_resource_and_query_targets_exist(self):
        meta=json.loads((ROOT/'site_metadata.json').read_text())
        prefix=meta['repository_url']
        for target in re.findall(r'href="([^"]+)"',self.html):
            for kind in ('blob','tree'):
                start=prefix+'/'+kind+'/'+meta['repository_branch']+'/'
                if target.startswith(start):
                    self.assertTrue((ROOT.parent/target[len(start):]).exists(),target)
        for query in self.data['queries']:
            for cohort in ('main9','studies7'):
                self.assertTrue((ROOT.parent/'data/reports'/cohort/query['id']).is_dir())
            self.assertTrue((ROOT.parent/'data/evaluation/main9/rubrics'/(query['id']+'.json')).is_file())
        self.assertEqual(self.html.count('class="resource-card"'),6)
        self.assertIn('PUBLIC RESOURCES',self.html)
        self.assertIn('available in the public repository',self.html)
        self.assertIn('id="query-jump"',self.html)
        self.assertIn('id="copy-citation"',self.html)

    def test_task_number_presentation_retains_source_attribution(self):
        self.assertNotIn('id="source-filter"', self.html)
        self.assertIn('Search task numbers, titles and original task text', self.html)
        self.assertIn('Task number (1–40), title, or text', self.html)
        self.assertIn('DRB-I: 6', self.html)
        self.assertIn('ResearchRubrics: 12', self.html)
        self.assertEqual(len({q['id'] for q in self.data['queries']}), 40)
        self.assertEqual({q['source'] for q in self.data['queries']}, {'drb1', 'drb2', 'rr'})

    def test_current_benchmark_inventory_and_criteria(self):
        self.assertEqual(self.data['manuscript']['date'],'2026-11-16')
        self.assertIn('16 November 2026',self.html)
        rows={r['component']:r for r in self.data['benchmark_resources']}
        for source,key in [('drb1','drb1'),('drb2','drb2'),('rr','researchrubrics')]:
            queries=[q for q in self.data['queries'] if q['source']==source]
            self.assertEqual(rows['All queries'][key],len(queries))
            self.assertEqual(rows['Chinese queries'][key],sum(q['language']=='zh' for q in queries))
            self.assertEqual(rows['Collected reports'][key],len(queries)*9)
            self.assertEqual(rows['Human-annotated report pairs'][key],len(queries)*2)
        rubrics=self.data['rubric_distribution']
        self.assertEqual([rubrics[-1][k] for k in ('pointwise','pairwise','total')],[776,323,1099])
        for key in ('pointwise','pairwise','total'):
            self.assertEqual(sum(r[key] for r in rubrics[:-1]),rubrics[-1][key])
        self.assertEqual(len(self.data['manuscript']['tables']),14)

    def test_script_and_stylesheet_versions_match_content(self):
        for name in ('index.html', 'leaderboard.html'):
            refs = re.findall(r'(?:src|href)="(assets/[^"?]+\.(?:js|css))\?v=([a-f0-9]{12})"', (DIST/name).read_text())
            self.assertGreaterEqual(len(refs), 5)
            for relative, version in refs:
                self.assertEqual(hashlib.sha256((DIST/relative).read_bytes()).hexdigest()[:12], version)

    def test_authors_are_collapsed_without_removing_attribution(self):
        opening, body = re.search(r'(<details[^>]*id="authors"[^>]*>)(.*?)</details>', self.html, re.S).groups()
        self.assertNotRegex(opening, r'\bopen(?:\s|=|>)')
        self.assertIn('<summary>Authors &amp; affiliations</summary>', body)
        meta = json.loads((ROOT/'site_metadata.json').read_text())
        for author in meta['authors']:
            self.assertIn(author['name'], body)
        for institution in meta['affiliations']:
            self.assertIn(institution, body)
        self.assertIn('Equal contribution', body)
        self.assertIn('Corresponding authors', body)

    def test_local_links_and_unique_ids(self):
        class Parse(HTMLParser):
            def __init__(self):
                super().__init__(); self.ids=[]; self.links=[]
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if 'id' in attrs:self.ids.append(attrs['id'])
                self.links += [attrs[k] for k in ('src','href') if k in attrs]
        for name in ('index.html','leaderboard.html'):
            parser=Parse(); parser.feed((DIST/name).read_text())
            self.assertEqual(len(parser.ids),len(set(parser.ids)))
            for link in parser.links:
                if link.startswith('#'):
                    self.assertIn(link[1:],parser.ids)
                elif not re.match(r'https?://',link):
                    path,_,fragment=link.partition('#')
                    target=DIST/path.split('?',1)[0]
                    self.assertTrue(target.is_file(),link)
                    if fragment:
                        other=Parse();other.feed(target.read_text())
                        self.assertIn(fragment,other.ids)


if __name__ == '__main__':
    unittest.main()

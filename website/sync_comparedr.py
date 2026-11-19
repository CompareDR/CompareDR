#!/usr/bin/env python3
"""Rebuild the local website from the frozen CompareDR manuscript. No API calls."""
import copy
import csv
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'manuscript'
DIST = ROOT / 'dist'
sys.path.insert(0, str(ROOT.parent / 'submissions'))
from attribution import site_notices, standalone_credits
SCORE_KEYS = ('D1', 'D2', 'D3', 'D4', 'D5_D6', 'overall')
PAPER = INPUT / 'source/main.tex'
TEX = PAPER.read_text()


def project_context(title):
    """Presentation metadata is separate from the frozen numerical manuscript."""
    meta = json.loads((ROOT / 'site_metadata.json').read_text())
    repository = meta['repository_url'].rstrip('/')
    assert repository.startswith('https://github.com/')
    assert meta['publication_status'] in ('private-preview', 'public')
    authors = []
    for author in meta['authors']:
        marks = [str(n) for n in author['affiliations']]
        if author.get('equal'):
            marks.append('*')
        if author.get('corresponding'):
            marks.append('†')
        authors.append(f'<span>{html.escape(author["name"])}<sup>{",".join(marks)}</sup></span>')
    affiliations = ''.join(f'<span><sup>{i}</sup> {html.escape(name)}</span>'
                           for i, name in enumerate(meta['affiliations'], 1))
    bibtex = ('@unpublished{wu2026comparedr,\n'
              '  title = {' + title + '},\n'
              '  author = {' + ' and '.join(a['name'] for a in meta['authors']) + '},\n'
              '  year = {' + meta['year'] + '},\n'
              '  note = {Manuscript}\n}\n')

    def resource_link(label, relative):
        target = ROOT.parent / relative
        assert target.exists(), f'Missing website resource: {relative}'
        kind = 'tree' if target.is_dir() else 'blob'
        return (f'<a href="{html.escape(repository)}/{kind}/{meta["repository_branch"]}/{relative}" '
                f'target="_blank" rel="noopener">{html.escape(label)}</a>')

    cards = [
        ('01 / EVALUATE', 'Run the evaluation',
         'Start with the portable CLI, then inspect the pipeline for graph construction, PT/PW judging, verification, and aggregation.',
         [('Setup & execution guide', 'evaluation/README.md'), ('Main entry · evaluation/run.py', 'evaluation/run.py'),
          ('Pipeline · evaluation/pipeline.py', 'evaluation/pipeline.py')]),
        ('02 / REPRODUCE', 'Reproduce the paper',
         'Recalculate all 16 numerical tables from frozen judgments, labels, and trials. Offline reproduction makes no model calls.',
         [('Experiment-to-code map', 'experiments/README.md'), ('Offline entry · experiments/run.py', 'experiments/run.py'),
          ('Verified numerical results', 'reproduction/results/verified_20261116/RESULTS.json')]),
        ('03 / MAIN RESULTS', 'Nine-system reports',
         '360 complete reports: 40 queries × 9 systems. Use this collection for the main leaderboard; the manifest binds each file to its identity and hashes.',
         [('Browse main9 reports', 'data/reports/main9'), ('Main9 manifest', 'data/reports/main9/manifest.json')]),
        ('04 / VALIDATION STUDIES', 'Seven-system reports',
         '280 reports: 40 queries × 7 systems. These are the independently frozen inputs for human-preference, component, and sampling studies.',
         [('Browse studies7 reports', 'data/reports/studies7'), ('Studies7 manifest', 'data/reports/studies7/manifest.json'),
          ('Cohort identities & schemas', 'docs/DATA.md')]),
        ('05 / CRITERIA & LABELS', 'Inspect the annotations',
         'Find all 1,099 criteria, 80 human-preference pairs, and the directions and target dimensions for 120 controlled revisions. Report identities are cohort-specific.',
         [('Queries, rubrics & guidelines', 'data/evaluation'), ('Human preference labels', 'data/annotations/human_preferences.json'),
          ('Controlled revision labels', 'data/annotations/controlled_revisions.json'),
          ('Base and revised reports', 'reproduction/materials/controlled_revisions')]),
        ('06 / PARTICIPATE', 'Evaluate another system',
         'Generate reports for the 40 frozen queries, package the outputs with model and harness settings, and run the format checker before maintainer review.',
         [('Submission format', 'submissions/README.md'), ('Offline format checker', 'submissions/validate.py')])]
    rendered = []
    for tag, heading, description, links in cards:
        items = ''.join('<li>' + resource_link(label, relative) + '</li>' for label, relative in links)
        rendered.append(f'<article class="resource-card"><span class="tag">{tag}</span><h3>{heading}</h3>'
                        f'<p>{description}</p><ul>{items}</ul></article>')
    paper_buttons = []
    for label, key in [('Paper', 'paper_url'), ('arXiv', 'arxiv_url')]:
        url = meta[key]
        if url:
            assert url.startswith('https://')
            paper_buttons.append(f'<a class="button secondary" href="{html.escape(url)}">{label} ↗</a>')
        else:
            paper_buttons.append(f'<span class="button unavailable" aria-disabled="true">{label} <small>not yet public</small></span>')
    return dict(AUTHORS=''.join(authors), AFFILIATIONS=affiliations,
                CITATION=html.escape(bibtex), PAPER_BUTTONS=''.join(paper_buttons),
                RESOURCE_CARDS=''.join(rendered), REPOSITORY_URL=html.escape(repository),
                REPOSITORY_TREE=html.escape(repository + '/tree/' + meta['repository_branch']),
                REPOSITORY_BLOB=html.escape(repository + '/blob/' + meta['repository_branch'])), bibtex


def clean(value):
    value = re.sub(r'\\(?:textbf|texttt|emph)\{([^{}]*)\}', r'\1', value)
    return value.replace(r'\%', '%').replace('$', '').strip()


def table(label):
    """Read data rows, not table numbers that change with manuscript layout."""
    for match in re.finditer(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', TEX, re.S):
        if r'\label{' + label + '}' not in match[0]:
            continue
        body = match[0].split(r'\midrule', 1)[1].split(r'\bottomrule', 1)[0]
        rows = []
        for row in body.split(r'\\'):
            row = row.replace(r'\midrule', '').strip()
            if '&' in row:
                rows.append([clean(cell) for cell in row.split('&')])
        return rows
    raise ValueError('Missing manuscript table: ' + label)


def number(value):
    return None if value in ('--', '---') else float(value.rstrip('%'))


def numeric_rows(label, names):
    return [dict(method=row[0], **{name: number(value) for name, value in zip(names, row[1:])})
            for row in table(label)]


def fraction(value):
    match = re.fullmatch(r'(\d+)/(\d+) \(([\d.]+)\)', value)
    assert match, value
    return dict(correct=int(match[1]), total=int(match[2]), percent=float(match[3]))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version_assets(page):
    """Avoid mixing updated HTML with a cached script or stylesheet."""
    return re.sub(r'(src|href)="(assets/[^"?]+\.(?:js|css))"',
        lambda m: f'{m[1]}="{m[2]}?v={digest(DIST / m[2])[:12]}"', page)


def leaderboard_rows(data):
    maximum = {key: max(row[key] for row in data['leaderboard']) for key in SCORE_KEYS}
    rows = []
    for row in sorted(data['leaderboard'], key=lambda r: (-r['overall'], r['rank'])):
        cells = []
        for key in SCORE_KEYS:
            css = ('total ' if key == 'overall' else '') + ('best' if row[key] == maximum[key] else '')
            cells.append(f'<td class="{css}">{row[key]:.2f}</td>')
        rows.append(f'<tr><td>{row["rank"]}</td><td><span class="model">{html.escape(row["model"])}</span>'
                    f'<span class="harness">{html.escape(row["harness"])}</span></td>{"".join(cells)}</tr>')
    return '\n'.join(rows)


def leaderboard_table(data):
    """One full-dimensional Markdown table for both repository entry points."""
    maximum = {key: max(row[key] for row in data['leaderboard']) for key in SCORE_KEYS}
    lines = ['| Rank | Research harness | Model | Responsiveness | Evidence | Reasoning | Synthesis | Readability | Overall |',
             '|---:|---|---|---:|---:|---:|---:|---:|---:|']
    for row in sorted(data['leaderboard'], key=lambda r: (-r['overall'], r['rank'])):
        values = [f'**{row[k]:.2f}**' if row[k] == maximum[k] else f'{row[k]:.2f}' for k in SCORE_KEYS]
        lines.append('| ' + ' | '.join([str(row['rank']), row['harness'], row['model']] + values) + ' |')
    return '\n'.join(lines)


def leaderboard_markdown(data):
    lines = ['# CompareDR Leaderboard', '',
        'Nine-system manuscript snapshot · 16 November 2026', '',
        '**40 queries per system · 360 reports · 1,440 within-query pairs · 1,099 criteria**', '',
        'Higher is better. Bold marks the column maximum, not a significance test.', '',
        leaderboard_table(data)]
    lines += ['', '## Evaluation protocol', '',
        '- Total: 30% Responsiveness + 30% Evidence + 10% Reasoning + 10% Synthesis + 20% Readability; equal query weights.',
        '- Primary judge: GPT-5.5, medium reasoning. External verification: deepseek-v4.1-flash, reasoning disabled.',
        '- Model and harness identify report generation, not the evaluator. DuMate did not disclose its underlying model; Kimi K3 uses the main-table label (collection setting: Kimi K3 Max).',
        '- Reference scale: 0–100, not factual-accuracy percentages. Pointwise and ordinal pairwise signals are combined where available.',
        '- Scores depend on the comparison pool. Adding a system requires a consistently aggregated, explicitly identified new cohort snapshot.',
        '- Display values are rounded to two decimals; exports retain full precision. Small score gaps alone do not establish significance.', '',
        '## Explore, reproduce, or participate', '',
        '- [Interactive leaderboard](website/dist/leaderboard.html) — open locally; overall and dimension sorting.',
        '- [CSV scores](website/dist/leaderboard.csv) · [JSON scores and protocol](website/dist/leaderboard.json).',
        '- [New-system participation guide](website/participation.md) — required reports, configuration, provenance, and integration steps.',
        '- [Offline reproduction](experiments/README.md) · [Evaluator](evaluation/README.md) · [Report and annotation resources](docs/DATA.md).', '',
        '[Submit a system](https://github.com/CompareDR/CompareDR/issues/new?template=submit-system.yml) · [Package format](submissions/README.md) · [Template ZIP](website/dist/submission-template.zip).', '',
        'Submit through the public GitHub issue form. Evaluation and score acceptance are coordinated by the maintainers, not performed automatically.', '',
        'Generated by `website/sync_comparedr.py` from the manuscript-aligned full-precision results; do not edit score cells by hand.', '']
    return '\n'.join(lines)


def refresh_package_hashes():
    paths = [p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.md', '.json', '.py', '.cjs')
             and p.name != 'PACKAGE_HASHES.json']
    for directory in ('baseline', 'dist', 'manuscript', 'templates'):
        paths.extend(p for p in (ROOT / directory).rglob('*') if p.is_file() and not p.name.startswith('.'))
    manifest = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    (ROOT / 'PACKAGE_HASHES.json').write_text(json.dumps(manifest, indent=2) + '\n')


def make_data():
    baseline = json.loads((INPUT / 'baseline_data.json').read_text())
    data = copy.deepcopy(baseline)
    title = re.search(r'^\\title\{([^\n]*)\}', TEX, re.M)[1]
    data.update(title=title, short_title='CompareDR',
                subtitle='from Individual Quality to Comparative Merit',
                release='Local preview · manuscript synchronized 2026-11-16')
    paper_board = table('tab:system_results')
    assert len(paper_board) == len(data['leaderboard']) == 9
    for row, paper_row in zip(data['leaderboard'], paper_board):
        # Retain the original full precision when the paper's rounded value agrees.
        assert row['harness'] == paper_row[1]
        row['model'] = '—' if paper_row[0] == '---' else paper_row[0]
        for key, value in zip(SCORE_KEYS, paper_row[2:]):
            assert f'{row[key]:.2f}' == f'{float(value):.2f}', (row, key, value)
    data['human_alignment'] = []
    for method, agreement, kappa, f1, ci in table('tab:human_agreement'):
        data['human_alignment'].append(dict(method=method, agreement=float(agreement),
            kappa=float(kappa), macro_f1=float(f1), ci=[float(x) for x in ci.split('--')]))
    data['ablations'] = numeric_rows('tab:ablations', ['agreement', 'kappa', 'macro_f1', 'delta'])
    robust = {r[0].replace(' (Primary)', ''): r[1:] for r in table('tab:cross-judge-robustness')}
    stability = {r[0].replace(' (Primary)', ''): r[1:] for r in table('tab:judge-stability')}
    data['cross_judge'] = []
    for judge, agreement, reversals, rho in table('tab:judge-selection'):
        icc, rank_rho, tau, query_rho, bias = map(number, robust[judge])
        assert number(rho) == rank_rho
        data['cross_judge'].append(dict(judge=judge, order_agreement=float(agreement),
            reversals=float(reversals), rho=rank_rho, icc=icc, tau=tau,
            mean_query_rho=query_rho, bias=bias, cycles=number(stability[judge][2])))
    rows = []
    for method, threshold, improvement, degradation, equivalent, acc, f1 in table('tab:controlled_response'):
        rows.append(dict(method=method, threshold=float(threshold), improvement=fraction(improvement),
            degradation=fraction(degradation), equivalent=fraction(equivalent),
            accuracy=float(acc), macro_f1=float(f1)))
    data['controlled_revisions'] = dict(queries=40, constructed=120, evaluated=119,
        excluded=1, label_type='Human-confirmed quality directions and target dimensions',
        calibration='Method-specific absolute thresholds optimized for macro-F1 on the same 119 revisions; not held-out performance.',
        framework_judge='deepseek-v4.1-flash', framework_reasoning='max',
        same_coverage_pt_judge='deepseek-v4.1-flash', same_coverage_pt_reasoning='max',
        race_judge='GPT-5.5', race_reasoning='medium',
        source_protocol_judges={'DRB-I':'GPT-5.5 medium', 'DRB-II':'Gemini 2.5 Pro provider default',
                               'ResearchRubrics':'Gemini 2.5 Pro provider default'}, rows=rows)
    data['controlled_thresholds'] = []
    for method, *cells in table('tab:controlled_thresholds'):
        row = dict(method=method)
        for key, cell in zip(('absolute_acc', 'absolute_f1', 'percentage_acc', 'percentage_f1'), cells):
            match = re.fullmatch(r'([\d.]+) \(([\d.]+)\)', cell)
            row[key] = dict(value=float(match[1]), threshold=float(match[2]))
        data['controlled_thresholds'].append(row)
    data['controlled_dimensions'] = [dict(dimension=r[0], n=int(r[1]),
        hybrid=fraction(r[2]), pointwise=fraction(r[3])) for r in table('tab:controlled_dimensions')]
    data['judge_pilot'] = [dict(metric=r[0], values=[v if '/' in v else float(v) for v in r[1:]])
        for r in table('tab:judge_pilot')]
    data['new_system_entry'] = [dict(opponents=r[0], new_pairs=int(r[1]), token_savings=number(r[2]),
        mae=float(r[3]), p95=float(r[4]), rank_accuracy=number(r[5])) for r in table('tab:new_system_sampling')]
    data['token_usage'] = [dict(model=r[0], responses=int(r[1].replace(',', '')),
        input_m=float(r[2]), output_m=float(r[3]), total_m=float(r[4]))
        for r in table('tab:token_usage')]
    data['human_dimension_agreement'] = dict(Responsiveness=65.00, Evidence=58.75,
        Reasoning=78.75, Synthesis=72.50, Readability=67.50)
    data['validation_scope'] = ('The leaderboard uses nine systems. Human-preference and component comparisons use 80 annotated pairs from the seven-system collection. Controlled revisions use 119 common human-confirmed revisions; cross-judge comparison uses 20 queries and four systems.')
    data['metric_provenance'] = 'Transcribed and checked by stable table labels against the 2026-11-16 CompareDR public manuscript; leaderboard exports retain the matching underlying full-precision scores.'
    data['leaderboard_protocol'].update(verifier='deepseek-v4.1-flash', verifier_reasoning='disabled')
    data['model_settings'] = dict(primary_judge='GPT-5.5', primary_reasoning='medium',
        component_judge='GPT-5.5', component_reasoning='medium',
        alternative_judge='deepseek-v4.1-flash', alternative_reasoning='max',
        alternative_display='DeepSeek-v4.1f', gemini_judge='Gemini 2.5 Pro',
        gemini_reasoning='provider default', kimi_generation_setting='Kimi K3 Max')
    data['benchmark_resources'] = [dict(component=r[0], drb1=int(r[1]), drb2=int(r[2]), researchrubrics=int(r[3]), total=int(r[4])) for r in table('tab:benchmark_resources')]
    data['rubric_distribution'] = [dict(dimension=r[0], focus=r[1], pointwise=int(r[2]), pairwise=int(r[3]), total=int(r[4].replace(',', ''))) for r in table('tab:rubric_distribution')]
    paper_manifest = json.loads((INPUT / 'source/PAPER_MANIFEST.json').read_text())
    data['manuscript'] = dict(version=paper_manifest['version'], date=paper_manifest['numerical_snapshot'],
        author_revision=paper_manifest['author_revision'],
        source_sha256=digest(PAPER), pdf_sha256=paper_manifest['files']['CompareDR.pdf'],
        tables={key: table(key) for key in ('tab:benchmark_resources','tab:rubric_distribution','tab:system_results', 'tab:human_agreement',
            'tab:controlled_response', 'tab:ablations', 'tab:judge-selection',
            'tab:cross-judge-robustness', 'tab:judge-stability', 'tab:judge_pilot',
            'tab:new_system_sampling', 'tab:token_usage', 'tab:controlled_dimensions',
            'tab:controlled_thresholds')})
    assert data['queries'] == baseline['queries']
    data['attribution'] = standalone_credits(data['queries'])
    assert data['domains'] == baseline['domains']
    return data


def build():
    # Build the query-only intake kit alongside the site; never include answer keys.
    from build_template import build as build_submission_template
    build_submission_template()
    for relative, content in site_notices().items():
        target = DIST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    data = make_data()
    presentation, bibtex = project_context(data['title'])
    assets = DIST / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    for name in ('style.css', 'table2_domain_distribution.svg'):
        shutil.copyfile(ROOT / 'baseline/assets' / name, assets / name)
    for name in ('framework.png', 'framework.pdf'):
        shutil.copyfile(ROOT.parent / 'docs/assets' / name, assets / name)
    (DIST / 'comparedr.bib').write_text(bibtex)
    (DIST / 'data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (assets / 'data.js').write_text('window.BENCH_DATA = ' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';\n')
    with (DIST / 'leaderboard.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data['leaderboard'][0]))
        writer.writeheader()
        writer.writerows(data['leaderboard'])
    (DIST / 'leaderboard.json').write_text(json.dumps(dict(
        benchmark='CompareDR', snapshot_date=data['manuscript']['date'],
        cohort='main9', systems=9, queries=40, reports=360, within_query_pairs=1440,
        score_scale=data['score_scale'], weights=data['weights'],
        protocol=data['leaderboard_protocol'],
        comparison_scope='Scores depend on the comparison pool; an added system requires a consistently aggregated expanded cohort.',
        rows=data['leaderboard']), ensure_ascii=False, indent=2) + '\n')
    shared_table = (ROOT / 'templates/leaderboard-table.html').read_text().replace(
        '{{LEADERBOARD_ROWS}}', leaderboard_rows(data))
    (ROOT.parent / 'LEADERBOARD.md').write_text(leaderboard_markdown(data))
    readme = ROOT.parent / 'README.md'
    if readme.is_file():
        text = readme.read_text()
        start, end = '<!-- LEADERBOARD_SUMMARY_START -->', '<!-- LEADERBOARD_SUMMARY_END -->'
        if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
            raise ValueError('README leaderboard markers are missing, duplicated, or reversed; refusing to leave a stale table')
        readme.write_text(text.split(start, 1)[0] + start + '\n' + leaderboard_table(data)
                          + '\n' + end + text.split(end, 1)[1])
    board_page = (ROOT / 'templates/leaderboard.html').read_text().replace('{{LEADERBOARD_TABLE}}', shared_table)
    for key, value in presentation.items():
        board_page = board_page.replace('{{' + key + '}}', value)
    (DIST / 'leaderboard.html').write_text(board_page)
    for name in ('leaderboard.js', 'leaderboard.css', 'project.css', 'project.js'):
        shutil.copyfile(ROOT / 'templates' / name, assets / name)
    shutil.copyfile(ROOT / 'participation.md', DIST / 'participation.md')
    format_text = (ROOT.parent / 'submissions/README.md').read_text()
    (DIST / 'submission-format.md').write_text(format_text.replace('../website/dist/submission-template.zip', 'submission-template.zip'))
    page = (ROOT / 'templates/index.html').read_text()
    page = page.replace('{{PAPER_TITLE}}', html.escape(data['title']))
    page = page.replace('{{LEADERBOARD_TABLE}}', shared_table)
    for key, value in presentation.items():
        page = page.replace('{{' + key + '}}', value)
    best = {key: max(data['leaderboard'], key=lambda row: row[key]) for key in ('overall', 'D3', 'D4', 'D5_D6')}
    page = page.replace('{{OVERALL_BEST}}', f"{best['overall']['overall']:.2f}")
    page = page.replace('{{INSIGHT_BEST}}', f"{best['D3']['D3']:.2f} / {best['D4']['D4']:.2f}")
    page = page.replace('{{READABILITY_BEST}}', f"{best['D5_D6']['D5_D6']:.2f}")
    (DIST / 'index.html').write_text(page)
    (assets / 'app.js').write_text((ROOT / 'templates/app.js').read_text())
    (DIST / 'experiment_results.json').write_text(json.dumps({key:data[key] for key in (
        'manuscript', 'benchmark_resources', 'rubric_distribution', 'model_settings', 'human_alignment', 'human_dimension_agreement',
        'ablations', 'cross_judge', 'judge_pilot', 'controlled_revisions',
        'controlled_thresholds', 'controlled_dimensions', 'new_system_entry', 'token_usage')}, indent=2) + '\n')
    for name in ('index.html', 'leaderboard.html'):
        target = DIST / name
        target.write_text(version_assets(target.read_text()))
    audit = dict(source='CompareDR '+data['manuscript']['version'], source_sha256=digest(PAPER),
        presentation_metadata_sha256=digest(ROOT / 'site_metadata.json'),
        figure_sha256={name:digest(ROOT.parent / 'docs/assets' / name) for name in ('framework.png', 'framework.pdf')},
        original_style_reference='baseline/assets',
        model_calls=0, publication='local only; no deployment performed',
        score_columns=list(SCORE_KEYS),
        repository_tables={name: digest(ROOT.parent/name) for name in ('README.md','LEADERBOARD.md')
                           if (ROOT.parent/name).is_file()},
        stylesheet_unchanged=digest(assets / 'style.css') == digest(ROOT / 'baseline/assets/style.css'),
        files={str(path.relative_to(ROOT)):digest(path) for path in sorted(DIST.rglob('*')) if path.is_file()})
    (INPUT / 'SYNC_AUDIT.json').write_text(json.dumps(audit, indent=2) + '\n')
    refresh_package_hashes()
    print(json.dumps(dict(status='built', title=data['title'], stylesheet_unchanged=audit['stylesheet_unchanged'],
        systems=len(data['leaderboard']), controlled_revisions=data['controlled_revisions']['evaluated'])))


if __name__ == '__main__':
    build()

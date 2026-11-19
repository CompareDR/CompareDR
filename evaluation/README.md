# Evaluation runtime

This directory contains the report-to-score pipeline and bundled dependencies.
Original prompts, validators, acquisition bounds and AB/BA semantics are retained.
Deployment paths and credentials are separated from research logic. Code hashes
are in [`SOURCE_INVENTORY.json`](SOURCE_INVENTORY.json).

## Validate without APIs

From the repository root:

```bash
python -B evaluation/run.py prepare --cohort main9 --out outputs/main9_run
python -B evaluation/run.py preflight --out outputs/main9_run
```

Use `--cohort studies7` and a separate output directory for that cohort. Preflight
reads complete reports, validates hashes and routing, binds references and writes
contracts. It makes no model/search calls. The MiniMax numbered-reference adapter
applies only to the matching R10 reports.

## Configure providers

Set these environment variables outside the repository before preparing an online
run. Never commit their values:

| Variable | Value |
|---|---|
| `COMPAREDR_JUDGE_ENDPOINT` | HTTPS chat-completions endpoint |
| `COMPAREDR_JUDGE_API_KEY` | Judge provider key |
| `COMPAREDR_VERIFIER_ENDPOINT` | HTTPS verifier chat-completions endpoint |
| `COMPAREDR_VERIFIER_API_KEY` | Verifier provider key |
| `COMPAREDR_SEARCH_ADAPTER` | `evaluation/search_serper.py`, or your own adapter |
| `SERPER_API_KEY` | Search provider key, if using the supplied Serper adapter |

`runtime_config.json` pins GPT-5.5 medium as main judge and deepseek-v4.1-flash
with thinking disabled as verifier, plus request/retry/concurrency budgets.
No provider availability is implied. The transport sends `model`, `messages`,
`max_tokens`, `stream:false`, and reasoning/thinking fields. A provider with a
different wire schema needs an explicit adapter; do not silently change models.

The search adapter exports `search(query, top_k, timeout)` returning a list of
`{"url": ..., "title": ..., "snippet": ...}` objects. It manages its own credential.
Snippets discover candidates, not verification evidence: source bodies are fetched
with public-address checks, deadlines and prohibited-source rules. PDF acquisition
requires `pdftotext` on PATH. Online runs require a configured search adapter.

The bundled [`search_serper.py`](search_serper.py) uses the public Serper search
interface and has no dependency beyond Python's standard library. Set
`COMPAREDR_SEARCH_ADAPTER=evaluation/search_serper.py` when running from the root.
Its request/response fields were checked against the
[CrewAI Serper integration](https://github.com/crewAIInc/crewAI-tools/blob/main/crewai_tools/tools/serper_dev_tool/serper_dev_tool.py).
It rejects redirects and never records raw provider error bodies. This portable
transport is not a claim that current search results equal the archived evidence.

## Execute and aggregate

```bash
python -B evaluation/run.py run --out outputs/main9_run --query drb1_19 --execute
# All 40 queries; separate processes, sequential by default.
python -B evaluation/run.py run --out outputs/main9_run --execute
python -B evaluation/run.py aggregate --out outputs/main9_run
```

`run` refuses model calls without `--execute`. Configuration changes require a new
prepared directory. Cached real responses are revalidated. Failed verification is
explicitly recorded and never converted into factual support; downstream judging
can continue under the supplied failure-accounting policy. Completion distinguishes
missing decisions from complete decisions with verification warnings.

The final aggregate fits the frozen five-level ordinal model (REG=.002), combines
available PT/PW channels and applies 30/30/10/10/20 weights equally over queries.
Per-query arithmetic diagnostics are **not** published leaderboard scores. The
numerical fitter retains the 40-query contract.

## Tests and boundaries

```bash
cd evaluation
python -B -m unittest test_formal test_integration test_provider
```

Tests use fake HTTP, covering nine-system execution, AB/BA order, cache resume,
graph failures, score gates, parsing, retries, authorization halts and fetch
protections. Keep runtime logs outside version control. Offline tests do not
certify access to live services or deterministic regeneration of model outputs.
Paper baseline decisions, component and controlled metrics are reproduced through
[`experiments/`](../experiments/README.md), without claiming fresh baseline API runs.

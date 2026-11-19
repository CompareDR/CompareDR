# LongCat research blog

Static bilingual blog with two accessible tabs: LongCat-DeepResearch and CompareDR.
This is an isolated addition; it does not overwrite the existing CompareDR website.

## Build and verify

Requires Node.js 20+ and the surrounding CompareDR checkout. No npm dependencies.

```sh
cd website/longcat-blog
npm run build
npm test
npm run validate-feed
npm run release-check
```

`dist/` is the **only** directory to send to the LongCat.ai deployment team.
Serve that directory over HTTP(S), not `file://`. Relative assets support a nested
blog URL without framework routing. The two tabs and language use `#technical`,
`#benchmark`, and `?lang=zh|en`. Do not ship the parent repository, raw reports,
private approval records, test fixtures, or Git history as website assets.

## Dynamic leaderboard: maintain data without redeploying the blog

The source of truth is `feed/v1/leaderboard.json`. Publish this file in the approved
public CompareDR organization repository. Once the actual repository exists,
configure its public HTTPS raw URL in `config.json` as `feedUrl`. The expected
path under a repository named CompareDR would be:

```text
https://raw.githubusercontent.com/CompareDR/CompareDR/main/website/longcat-blog/feed/v1/leaderboard.json
```

This is the configured public data destination in the CompareDR organization.
Do not point at a private endpoint, add an access token, or use the GitHub blob UI
as a JSON URL. GitHub Pages is also supported when its public JSON endpoint is
configured. Only explicitly allowed HTTPS origins are accepted.

After the first deployment, update just the JSON file through review. Run
`npm run validate-feed` before merging. Every change requires a new `revision`;
set `snapshot_date` to the actual result snapshot date. Publish the complete
cohort, all five dimensions, weights, judge settings, and counts atomically.
Adding a system requires reaggregating the expanded comparison pool, not merely
appending an independently scored row. Store historical revisions in Git.

The frontend fetches on page load and manual refresh, with a six-second timeout,
`credentials: omit`, `cache: no-store`, a size limit, strict validation, and
text-only rendering. No access tokens, remote scripts, browser persistence, or
continuous polling. A failed refresh preserves the last validated in-memory
snapshot; a failed first load displays the bundled snapshot and its date. Older
dates and reuse of a revision for different data are rejected. An intentional
rollback should be published as a new revision with an appropriate snapshot date.
Raw GitHub/CDN propagation is not instantaneous; confirm the displayed revision.

JSON and CSV downloads always describe the currently displayed cohort. Original
paper counts in the article remain fixed and are explicitly labeled as paper
results; the dynamic table has its own current counts and protocol.

## Deployment integration

- Deploy all of `dist/`, including local assets and notices. No backend is required.
- Allow outbound browser `connect-src https://raw.githubusercontent.com` (or the
  configured GitHub Pages origin) in the host CSP. Keep `script-src 'self'` and
  `img-src 'self'`; the tiny CSS chevron additionally needs `data:` for images.
- Set JS MIME types correctly, including `.mjs` as `text/javascript`.
- The remote JSON endpoint must permit CORS reads from the LongCat origin. Do not
  use `no-cors`: an opaque response cannot supply leaderboard data.
- If reader networks cannot reach GitHub reliably, the hosting team can provide a
  same-site read-only mirror/reverse proxy with a fixed upstream and cache TTL.
  That is an infrastructure change, not a browser security workaround; configure
  the exact allowed mirror origin before using it.
- Test both language/tab routes, every sort key, download parity, and a blocked
  network update on the actual LongCat deployment before announcement.

## Resource publication

The code and versioned data feed are maintained in
[CompareDR/CompareDR](https://github.com/CompareDR/CompareDR).

The LongCat technical report and code links are verified public links. Its
Hugging Face paper page is **not** a dataset, so it is not presented as one.
For CompareDR, fill in `benchmarkCode`, `benchmarkPaper`, `benchmarkData`, and
optional explorer/submission links only after verifying their final URLs.
The release check intentionally fails until those links and a public valid feed
are present. The public-facing page says only “coming soon”; it does not reveal
internal approvals or historical experimental variants.

Copyright (c) 2026 LongCat.
CompareDR uses Apache-2.0 for project-owned code and CC BY
4.0 for original data contributions, with original third-party terms retained.
This blog README is not a substitute for the repository's effective LICENSE,
dataset attribution, or the separate arXiv submission license selection.

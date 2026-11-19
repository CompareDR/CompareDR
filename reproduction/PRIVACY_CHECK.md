# Package privacy and credential screening

The distribution is screened locally before delivery and again after extraction
from the ZIP. No files are uploaded by this process.

## Scope

- Every packaged file is read; unknown binary files and symbolic links are blocked.
- Credential checks cover app/client IDs, API keys, bearer and access/refresh tokens,
  JWTs, cookies, session identifiers, private keys and credential-bearing URL parameters.
- JSON fields and Python constant assignments are inspected in addition to text
  patterns and long high-entropy strings.
- Local usernames and filesystem paths, internal hosts/private IPs, private chat
  links, hidden configuration files and operating-system sidecar files are checked.
- ZIP filenames, contents, checksums, entry attributes and extra fields are checked;
  the ZIP is assembled without local-owner metadata or extended attributes.

No unresolved credential or local-privacy findings remain in the delivered package.
Flagged citation URLs and code syntax are reviewed rather than silently ignored.
Public UN document identifiers, dictionary lookup terms and website `/home/` paths
are retained. A NumPy matrix-multiplication expression is not an email address.

## Minimization

Citation-link tracking parameters are removed: 1,668 `utm_source` occurrences and
5 `srsltid` occurrences. No deleted parameter values are included in the project.
This affects link text in 52 report files and the benchmark input; the associated
query-hash metadata is updated separately. One query, DRB-II 75, contains such a
source link. Its substantive text is unchanged; original and distributed query
hashes are both recorded. See `materials/DISTRIBUTION_TRANSFORMS.json`.

Report `sha256` fields identify the original evaluation input; `file_sha256` fields
verify distributed bytes. Scientific labels, numeric inputs and numerical outputs
are unchanged. Token-usage counts are retained as experimental statistics; they
are not access tokens.

## Limits

This is a credential/local-privacy screening, not a guarantee against every possible
unknown secret format, a de-identification study of all people mentioned in public
research reports, or a redistribution-license review. Published author information,
benchmark content and public-source citations are not treated as local credentials.

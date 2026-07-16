# Publication Plan

## Publication mode

The primary publication will be an independently authored public policy
research brief tracked in this repository in Markdown and published as a
disclosure-reviewed PDF release asset. The PDF will not be committed to Git.
The brief will analyze the legislative and regulatory policy relevance of
observed removal-request patterns and evidence limitations affecting
open-source software infrastructure.

The intended audience is legislators, regulatory staff, public-interest
technology-policy researchers, and open-source ecosystem stewards. The brief
will inform policy evaluation; it will not provide legal advice or present
policy conclusions beyond what the bounded Lumen sample supports.

The release will include:

- An executive summary and clearly bounded findings.
- The final research protocol and amendment log.
- A methodology and limitations section.
- Disclosure-reviewed aggregate tables.
- A policy analysis section that separates observed evidence, data limitations,
  and bounded implications for transparency and accountability policy.
- A privacy-minimized source index sufficient to audit material claims within
  the public-data boundary.
- Reproducibility code and instructions.
- The required Lumen attribution and non-endorsement notice.

After publication, the release is planned to be archived through Zenodo to
obtain a stable DOI and citable version. Later corrections will be issued as
new versions rather than silently replacing the cited release.

## Editorial standards

The brief will separate source facts, deterministic calculations, researcher
interpretation, policy implications, and unresolved uncertainty. It will avoid
legal conclusions, claims of comprehensive coverage, validity judgments about
notices or named parties, and recommendations that exceed the evidence.

Material factual claims will be traceable to an aggregate computation, the
[versioned query manifest](manifests/query-manifest.v0.1-draft.json), or a Lumen
notice identifier. Policy analysis will identify the evidence and limitations
on which it relies. Draft findings will receive a manual source audit before
publication.

Repository contract checks run with:

```sh
python3 scripts/validate_repository.py
```

## Planned release artifacts

| Artifact | Format | Publication status |
|---|---|---|
| Research protocol | Markdown in Git; PDF appendix as a release asset | Public |
| Public policy research brief | Markdown in Git; PDF release and archive asset | Public |
| Aggregate tables | CSV and documented data dictionary | Public after disclosure review |
| Query manifest | JSON or YAML | Public without credentials |
| Source index | CSV or JSONL | Public after minimization review |
| Raw API responses | Original API format | Local only; never committed |

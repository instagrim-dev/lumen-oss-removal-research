# Lumen OSS Removal Research

Public research protocol and reproducibility materials for a legislative and
regulatory policy-focused study of legal complaints and removal requests that
reference selected open-source software development and distribution
ecosystems.

## Project status

**Protocol draft; Lumen researcher access is pending.** Data collection has not
started, and this repository makes no research findings.

The initial study is designed as a bounded, descriptive pilot whose evidence
will inform a public policy analysis of transparency and accountability in
online removal-request processes. It will not try to measure every removal
request involving open-source software, authenticate the provenance of notices,
determine whether allegations are valid, provide legal advice, or claim policy
conclusions that the collected evidence cannot support.

## Planned outputs

- A preregistered research protocol and [versioned draft query manifest](manifests/query-manifest.v0.1-draft.json).
- A public policy research brief in tracked Markdown and a release-asset PDF.
- Aggregate tables and a methodology appendix.
- Reproducibility code that does not contain credentials or restricted raw
  material.
- A permanently archived release with a DOI.

Raw API responses, authentication credentials, and unnecessary complained-of
URLs will not be published in this repository. See [DATA_HANDLING.md](DATA_HANDLING.md).

## Research question

How are online removal requests represented in the Lumen Database associated
with selected open-source software projects and distribution ecosystems, and
what descriptive patterns appear across notice type, sender, recipient,
jurisdiction, timing, and reported or requested action?

What limitations and transparency gaps should legislators, regulators, and
public-interest technology-policy researchers account for when evaluating
removal-request policy affecting open-source software infrastructure?

The full study design and its limitations are in
[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md).

## Publication plan

This repository is the primary public publication surface. The completed
public policy research brief will be tracked here in Markdown;
disclosure-reviewed PDFs will be attached to releases and archived through
Zenodo rather than committed to Git. Its intended audience is legislators,
regulatory staff, public-interest technology-policy researchers, and
open-source ecosystem stewards. See
[PUBLICATION_PLAN.md](PUBLICATION_PLAN.md).

## Researcher

Jonathan Maye-Hobbs is the independent researcher. He is a software engineer
and open-source maintainer whose public work focuses on developer tooling,
cloud infrastructure, and agent coordination.

- GitHub: https://github.com/instagrim-dev
- Contact: hobbs@jmh.llc
- Public verification and selected technical work: [VERIFICATION.md](VERIFICATION.md)

JMH Blockchain, LLC is his professional affiliation. The study is independently
conducted and has no client or institutional sponsor.

## Lumen disclosure

Lumen researcher access is pending, and the project has not used the Lumen API.
Any future API-derived public policy research brief will include the required
disclosure exactly as follows:

> This product uses the Lumen API but is not endorsed or certified by Lumen.

For any future API-derived findings, Lumen will be identified as the source of
the underlying notice data. Inclusion of a notice in Lumen does not establish
its authenticity, the validity of its allegations, or whether the recipient
acted on it.

## Repository validation

Validate the protocol, draft query manifest, public identity contract, and
repository safety rules with:

```sh
python3 scripts/validate_repository.py
```

## License

Unless otherwise noted, original research materials in this repository are
licensed under the [Creative Commons Attribution 4.0 International License](LICENSE.md).

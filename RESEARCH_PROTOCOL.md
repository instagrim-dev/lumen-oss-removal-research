# Removal Requests and the Open-Source Software Supply Chain

## Protocol metadata

- **Status:** Draft; API access pending
- **Version:** 0.1
- **Date:** 2026-07-15
- **Researcher:** Jonathan Maye-Hobbs
- **Research posture:** Independent legislative and regulatory policy-focused
  public research
- **Primary artifact:** Public policy research brief
- **Primary audiences:** Legislative and regulatory staff, technology-policy
  researchers, and open-source software governance bodies

No data collection has begun. Material changes made after collection starts
will be recorded in a protocol amendment log before affected results are
published.

## Purpose

This study will describe removal requests represented in the Lumen Database
that reference selected open-source software development and distribution
ecosystems. The study is exploratory and descriptive. It is not designed to
estimate the total prevalence of removal requests affecting all open-source
software.

The work is intended to support policy-focused public understanding of how
legal complaints and removal mechanisms intersect with software repositories,
package registries, project domains, and related distribution infrastructure.
The primary artifact is a public policy research brief for legislative and
regulatory staff, technology-policy researchers, and open-source software
governance bodies.

## Research questions

1. What types of removal requests reference the selected ecosystems?
2. What patterns appear in notice type, sender, recipient, jurisdiction, date,
   and reported or requested action?
3. How do observed patterns vary across the selected ecosystems and study
   period?
4. Which recurring notice characteristics warrant careful qualitative
   description without implying legal validity or causation?
5. What limitations in search coverage, submission behavior, redaction,
   classification, and sampling constrain interpretation?
6. What do the observable records show, and fail to show, about transparency
   and oversight of removal-request processes affecting open-source software
   ecosystems?
7. Which metadata limitations constrain legislative, regulatory, and governance
   analysis of who requested an action, what action was reported or requested,
   what action was actually taken, and what state the Lumen record represents?

## Initial study frame

The provisional study interval is 2021-01-01 through 2025-12-31. That interval
is not operative and must not be described as a received-date interval until an
approved query manifest binds the exact Lumen API date field, states who or
what the field describes, specifies its timezone and inclusive or exclusive
boundaries, and defines how missing dates are handled.

Candidate ecosystem identifiers will be drawn from a bounded, versioned list
covering:

- Public source-code hosting services.
- Language package registries.
- Container-image distribution services.
- Project-controlled domains for a limited set of documented case studies.

The initial query manifest will identify exact hostnames, names, aliases, date
ranges, and exclusions before authenticated collection begins. Candidate
identifiers are not automatically treated as included merely because they are
found in repository metadata.

## Pre-collection requirements

Before collection, the researcher will publish a versioned query manifest
containing:

- The research question and intended public output.
- Exact query terms and facets.
- Study dates and pagination limits.
- Inclusion and exclusion rules.
- The maximum number of notices to retrieve.
- Known sources of false positives and false negatives.
- Exact API field bindings and semantics for dates, jurisdiction, country,
  reported or requested action, action actually taken, and Lumen record state.
- Publication-minimization rules and the comparisons permitted by field
  coverage and missingness.

Authenticated requests will not begin until that manifest has been reviewed,
validated, and marked approved. Approval requires the approver, approval
timestamp, source commit, content SHA-256 digest, and a passing
manifest-validator record. A draft or incomplete approval record is
non-operative. Any expanded query or material field-semantic change requires a
new manifest version and approval record. The current non-operative draft is
[query-manifest.v0.1-draft.json](manifests/query-manifest.v0.1-draft.json).

## Collection method

Collection will use read-only Lumen search and notice-retrieval endpoints.
Credentials will be supplied from the local process environment and will not
be stored in query manifests, command arguments, source files, or published
artifacts.

The collector will:

- Send a project-specific user agent and the required authentication header.
- Wait at least one second between API requests.
- Default to no more than 500 retrieved notices per run.
- Enforce an absolute ceiling of 1,000 retrieved notices per run.
- Stop and require a narrower manifest when the ceiling would be exceeded.
- Record retrieval timestamps, response status, pagination, errors, and
  truncation without recording the authentication token.
- Never submit notices or other data to Lumen.
- Never follow complained-of URLs automatically.

## Inclusion and exclusion

A notice may be included when the returned notice data contains an approved
identifier and passes the manifest's relevance rules. A hostname or project
name match alone will not establish that the notice concerns the open-source
project itself.

The study will exclude:

- Matches that cannot be tied to an approved ecosystem or case-study scope.
- Duplicate results identified by stable notice identity.
- Records outside the approved date interval.
- Material requiring automated traversal of complained-of URLs.
- Records whose publication would unnecessarily expose personal or sensitive
  information.

Ambiguous records may be retained only in an explicitly labeled uncertainty
category and will not contribute to stronger project-specific claims.

## Analysis

Deterministic processing will produce descriptive counts and tables only for
approved fields whose semantics and missingness rules are bound in the query
manifest. Planned dimensions include:

- Notice type and Lumen topic.
- The approved date field and study interval, described using the field's
  actual subject, timezone, boundary, and missing-date semantics.
- Sender and recipient as represented by Lumen.
- Jurisdiction metadata, with the manifest identifying which party, notice,
  legal authority, or record the field describes.
- Country metadata, separately bound to the party, notice, legal authority, or
  record it describes; country will not be treated as a synonym or proxy for
  jurisdiction.
- Reported or requested action, explicitly limited to what the notice or Lumen
  record says was requested or reported.
- Action actually taken, only when a separately bound field and its source
  semantics support that claim.
- Lumen record state, treated separately from both a requested action and an
  action actually taken.
- Selected ecosystem and inclusion confidence.

The study will not calculate or compare action rates until the approved
manifest fixes source-coverage and missingness denominators by provider or
recipient, time period, notice type, and ecosystem, and establishes that the
compared groups use sufficiently comparable reporting semantics. Missing or
unreported action data will not be interpreted as no action.

A bounded qualitative sample may be reviewed to describe recurring notice
characteristics. Sampling rules and sample size will be fixed in the query
manifest or a protocol amendment before qualitative claims are drafted.

Every quantitative claim must trace to deterministic output. Notice-level
examples may be published only when they can be supported through the minimized
source-index contract below without exposing unnecessary sensitive material.

## Evidence and reproducibility

Public reproducibility materials will include:

- The approved query manifest and its version history.
- Collector and deterministic analysis source code.
- Aggregate, disclosure-reviewed tables.
- A minimized source index containing a Lumen notice identifier and only the
  bounded, derived inclusion basis needed to understand why the record entered
  the study.
- Methodology, exclusions, errors, truncation, and uncertainty disclosures.

Raw responses will remain local, access-controlled working material and will
not be committed. The public source index will not include raw or bulk URLs,
raw notice text, or other fields merely because they would make a claim easier
to audit. Privacy and data minimization take precedence over claim-level
auditability: a claim that cannot be supported safely will be omitted or
weakened rather than publishing restricted or unnecessary data.

## Interpretation limits

The study will not infer that:

- A notice in Lumen is authentic, complete, accurate, or legally valid.
- A named party acted improperly merely because it appears in a notice.
- Lumen contains every relevant removal request.
- Search-result frequency measures the real-world incidence of infringement,
  abuse, censorship, or lawful removal.
- Correlation across dates, entities, or ecosystems establishes causation.

Results will be described as observations from the approved Lumen sample, not
as comprehensive claims about the open-source ecosystem.

## Ethics and data handling

The project will minimize collection and publication of sensitive material.
It will use only the fields necessary to answer the approved questions, keep
raw responses outside version control, and review public artifacts for
credentials, unnecessary personal information, and complained-of URLs.

Any decision to follow a URL returned by Lumen would require a separate,
documented lawful-use review. Automated link traversal is outside this
protocol.

## Publication and disclosure

The primary output will be a public policy research brief tracked in Markdown
in this repository, with a disclosure-reviewed PDF published as a release and
Zenodo asset rather than committed to Git. It is intended for legislative and
regulatory staff, technology-policy researchers, and open-source software
governance bodies. The public policy research brief will include this
disclosure:

> This product uses the Lumen API but is not endorsed or certified by Lumen.

The public policy research brief will identify Lumen as the source of notice
data and will explain that inclusion in Lumen does not authenticate a notice or
validate its claims.

## Change control

Before collection, edits may be made directly with a version-history note.
After collection begins, any change affecting the study frame, query terms,
field semantics, missingness rules, inclusion rules, ceilings, sampling,
analysis, or publication boundary will be recorded as an amendment containing:

- The date and reason for the change.
- Whether the change was made before or after inspecting affected results.
- Which outputs must be regenerated.
- How the change affects comparability with earlier runs.

# Data Handling and Credential Safety

## Data classes

| Class | Examples | Repository policy |
|---|---|---|
| Public protocol | Questions, scope, query terms, limits | Commit and publish |
| Public derived evidence | Aggregate tables, minimized source index | Publish after disclosure review |
| Restricted working data | Raw API responses, unreviewed notice fields | Local only; never commit |
| Secret | Lumen API token or other credentials | Environment or credential store only |

## Minimization precedence

Privacy and data minimization take precedence over public auditability. The
project will omit or weaken a claim when supporting it would require publishing
restricted working data, unnecessary personal information, raw notice text, or
raw or bulk complained-of URLs.

The public source index is limited to:

- The Lumen notice identifier.
- A bounded, derived inclusion basis whose allowed categorical values are fixed
  in the approved query manifest.

The inclusion basis must not reproduce raw query matches, notice text, personal
information, or URLs. A notice identifier is an audit pointer, not permission
to republish every field in the underlying record.

## Credential rules

- Use `LUMEN_API_TOKEN` as the local environment-variable name.
- Never place the token in a URL, query parameter, query manifest, command
  argument, source file, notebook, test fixture, or report.
- Send authentication through the API header required by Lumen.
- Use synthetic canary values for credential-leak tests.
- Rotate the token and remove affected history immediately if exposure is
  suspected.

## Raw-data rules

- Store raw responses outside version control in an access-controlled local
  directory.
- Do not publish bulk complained-of URLs or fields unnecessary for claim
  verification.
- Generate public tables from a minimized intermediate representation.
- Treat redaction as a review aid, not a substitute for data minimization.
- Do not follow complained-of URLs automatically.
- Bind each public field to an approved manifest field definition and
  missingness rule before generating it.
- Keep Git history text-only. Publish disclosure-reviewed PDFs as release or
  archive assets; never commit PDFs, images, or other binary artifacts.

## Publication review

Before any release:

1. Scan the repository and generated artifacts for secrets.
2. Confirm raw-data directories remain ignored and untracked.
3. Confirm the source index contains only notice identifiers and approved,
   bounded derived inclusion-basis values.
4. Review every public artifact for raw or bulk URLs, raw notice text,
   unnecessary personal information, and fields not approved by the manifest.
5. Trace every quantitative claim to deterministic output and omit or weaken
   claims that cannot be supported safely.
6. Trace each published example to a Lumen notice identifier without expanding
   the public source-index contract.
7. Confirm the manifest approval record contains an approver, timestamp, source
   commit, content SHA-256 digest, and passing validator result.
8. Include the Lumen attribution and non-endorsement disclosure.

## Incident response

If restricted data or a credential is committed, stop publication, revoke or
rotate the credential, remove the material from public history using an
appropriate incident process, and document the effect on research outputs.

# Query Manifests

Query manifests are the machine-readable approval boundary for collection and
analysis. A manifest is non-operative unless all query identifiers and field
semantics are bound, the terms review is complete, and its approval record
contains an approver, timestamp, source commit, content SHA-256 digest, and
passing validator result.

The `source_commit` is an already-existing commit containing the reviewed
protocol and query inputs; it is not a self-reference to the commit that records
approval. The content digest binds the complete approved manifest.

`query-manifest.v0.1-draft.json` is non-operative. Lumen access is pending,
authenticated collection is prohibited, query identifiers are empty, API field
semantics are unbound, and the collector is unavailable. Collection cannot
begin until these requirements are satisfied and the manifest is approved.

Privacy and data minimization override auditability throughout the manifest
lifecycle. Public source indexes are limited to a Lumen notice identifier and
an approved, bounded derived inclusion basis; raw or bulk URLs and raw notice
text are never public manifest outputs.

The repository is text-only. `allowed_binary_artifacts` must remain empty;
disclosure-reviewed PDFs are published outside Git as release and archive
assets.

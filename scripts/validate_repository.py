#!/usr/bin/env python3
"""Validate the public research contract without third-party dependencies."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


LEGAL_NAME = "JMH Blockchain, LLC"
# Keep the forbidden value out of this validator's own public source text.
STALE_LEGAL_NAME = "JMH" + ", LLC"
MANIFEST_PATH = Path("manifests/query-manifest.v0.1-draft.json")
LUMEN_DISCLOSURE = (
    "This product uses the Lumen API but is not endorsed or certified by Lumen."
)
REQUIRED_FILES = (
    Path("README.md"),
    Path("RESEARCH_PROTOCOL.md"),
    Path("DATA_HANDLING.md"),
    Path("PUBLICATION_PLAN.md"),
    Path("CITATION.cff"),
    Path("LICENSE.md"),
    Path("data/README.md"),
    Path("reports/README.md"),
    Path("VERIFICATION.md"),
    Path("manifests/README.md"),
    MANIFEST_PATH,
)
PUBLIC_SUFFIXES = {
    ".cff",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache"}
LOCAL_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EIN_RE = re.compile(r"(?<!\d)\d{2}-\d{7}(?!\d)")
SECRET_PATTERNS = (
    ("OpenAI-style token", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[A-Z0-9]{16}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "assigned Lumen token",
        re.compile(
            r"\bLUMEN_API_TOKEN\s*[:=]\s*['\"]?(?![<$\{])[^\s'\"#]{8,}",
            re.IGNORECASE,
        ),
    ),
)
REQUIRED_ACTION_BREAKDOWNS = {
    "submitter",
    "recipient",
    "notice_type",
    "study_interval",
    "ecosystem",
}
REQUIRED_FIELD_SEMANTICS = {
    "notice_type",
    "topic",
    "sender",
    "recipient",
    "jurisdiction",
    "country",
    "ecosystem",
    "inclusion_confidence",
}
REQUIRED_ACTION_BINDINGS = {
    "reported_or_requested_action",
    "action_actually_taken",
    "lumen_record_state",
}
REQUIRED_DENOMINATOR_STRATA = {
    "provider_or_recipient",
    "time_period",
    "notice_type",
    "ecosystem",
}
REQUIRED_SOURCE_INDEX_FIELDS = {"lumen_notice_id", "derived_inclusion_basis"}
REQUIRED_FORBIDDEN_PUBLIC_CONTENT = {
    "raw_urls",
    "bulk_urls",
    "raw_notice_text",
    "raw_query_matches",
    "unnecessary_personal_information",
}
ALLOWED_EXTENSIONLESS_FILES = {".gitignore"}
SENSITIVE_IDENTITY_FILENAME_RE = re.compile(
    r"(?:^|[^a-z0-9])(?:ein|cp[-_ ]?575|good[-_ ]?standing|certificate)(?:[^a-z0-9]|$)",
    re.IGNORECASE,
)
SENSITIVE_IDENTITY_CONTENT_RE = re.compile(
    r"\b(?:IRS\s+CP\s*575|Employer Identification Number|Certificate of Good Standing)\b",
    re.IGNORECASE,
)
IDENTITY_CONTROL_FILES = {
    Path("VERIFICATION.md"),
    Path("scripts/validate_repository.py"),
    Path("tests/test_validate_repository.py"),
}
TERMS_REVIEW_MAX_AGE_DAYS = 90


def _repository_files(root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode == 0:
        paths = [
            root / raw.decode("utf-8") for raw in result.stdout.split(b"\0") if raw
        ]
    else:
        paths = [path for path in root.rglob("*") if path.is_file()]
    return sorted(
        path
        for path in paths
        if path.is_file()
        and not EXCLUDED_PARTS.intersection(path.relative_to(root).parts)
    )


def _public_files(root: Path) -> list[Path]:
    return [
        path
        for path in _repository_files(root)
        if path.suffix.lower() in PUBLIC_SUFFIXES
        or path.name in ALLOWED_EXTENSIONLESS_FILES
    ]


def _read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{path}: cannot read public text: {exc}")
        return ""


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def manifest_content_sha256(manifest: dict[str, object]) -> str:
    """Return the canonical digest with the digest field itself cleared."""

    canonical = copy.deepcopy(manifest)
    approval = canonical.get("approval")
    if isinstance(approval, dict):
        approval["content_sha256"] = None
    payload = json.dumps(
        canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _parse_review_date(value: object) -> dt.date | None:
    if not _nonempty_string(value):
        return None
    text = str(value).strip()
    try:
        if "T" in text:
            normalized = text.replace("Z", "+00:00")
            return dt.datetime.fromisoformat(normalized).date()
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def _validate_field_semantics(
    manifest: dict[str, object], *, approved: bool, errors: list[str]
) -> None:
    semantics = manifest.get("field_semantics")
    if not isinstance(semantics, dict):
        errors.append("manifest: field_semantics must be an object")
        return

    date_entry = semantics.get("date")
    if not isinstance(date_entry, dict):
        errors.append("manifest: field_semantics.date must be an object")
    elif approved:
        if date_entry.get("status") != "bound":
            errors.append(
                "manifest: approved field_semantics.date.status must be 'bound'"
            )
        for key in (
            "source_field",
            "definition",
            "describes",
            "timezone",
            "missing_date_handling",
        ):
            if not _nonempty_string(date_entry.get(key)):
                errors.append(
                    f"manifest: approved field_semantics.date.{key} must be non-empty"
                )
        for key in ("start_inclusive", "end_inclusive"):
            if not isinstance(date_entry.get(key), bool):
                errors.append(
                    f"manifest: approved field_semantics.date.{key} must be boolean"
                )

    for name in sorted(REQUIRED_FIELD_SEMANTICS):
        entry = semantics.get(name)
        if not isinstance(entry, dict):
            errors.append(f"manifest: field_semantics.{name} must be an object")
            continue
        if approved:
            if entry.get("status") != "bound":
                errors.append(
                    f"manifest: approved field_semantics.{name}.status must be 'bound'"
                )
            for key in ("source_field", "definition", "missing_value_handling"):
                if not _nonempty_string(entry.get(key)):
                    errors.append(
                        f"manifest: approved field_semantics.{name}.{key} "
                        "must be non-empty"
                    )
            if name in {"jurisdiction", "country"} and not _nonempty_string(
                entry.get("describes_party_notice_authority_or_record")
            ):
                errors.append(
                    f"manifest: approved field_semantics.{name}."
                    "describes_party_notice_authority_or_record must be non-empty"
                )

    action = semantics.get("action")
    if not isinstance(action, dict):
        errors.append("manifest: field_semantics.action must be an object")
        return
    if approved and action.get("status") != "bound":
        errors.append(
            "manifest: approved field_semantics.action.status must be 'bound'"
        )
    action_bindings_ready = True
    for name in sorted(REQUIRED_ACTION_BINDINGS):
        binding = action.get(name)
        if not isinstance(binding, dict):
            errors.append(f"manifest: field_semantics.action.{name} must be an object")
            action_bindings_ready = False
            continue
        if approved:
            for key in (
                "source_field",
                "definition",
                "source_owner",
                "missing_value_handling",
            ):
                if not _nonempty_string(binding.get(key)):
                    errors.append(
                        f"manifest: approved field_semantics.action.{name}.{key} "
                        "must be non-empty"
                    )
                    action_bindings_ready = False
    breakdowns = action.get("missingness_breakdowns")
    breakdown_set = (
        {
            value.strip()
            for value in breakdowns
            if isinstance(value, str) and value.strip()
        }
        if isinstance(breakdowns, list)
        else set()
    )
    action_ready = (
        action_bindings_ready
        and _nonempty_string(action.get("coverage_rule"))
        and REQUIRED_ACTION_BREAKDOWNS.issubset(breakdown_set)
    )
    comparisons_enabled = action.get("comparisons_enabled")
    if not isinstance(comparisons_enabled, bool):
        errors.append(
            "manifest: field_semantics.action.comparisons_enabled must be boolean"
        )
    elif comparisons_enabled and not action_ready:
        errors.append(
            "manifest: action comparisons require a source-field mapping, "
            "definition, coverage rule, and submitter/recipient/notice_type/"
            "study_interval/ecosystem missingness breakdowns"
        )
    if approved and not action_ready:
        errors.append(
            "manifest: approved action semantics require coverage_rule and "
            "submitter/recipient/notice_type/study_interval/ecosystem "
            "missingness breakdowns"
        )
    elif (
        comparisons_enabled
        and action.get("comparison_basis") not in REQUIRED_ACTION_BINDINGS
    ):
        errors.append(
            "manifest: action comparisons require comparison_basis to name one "
            "separately bound action field"
        )
    if approved:
        source_fields = [
            str(action[name]["source_field"]).strip()
            for name in sorted(REQUIRED_ACTION_BINDINGS)
            if isinstance(action.get(name), dict)
            and _nonempty_string(action[name].get("source_field"))
        ]
        if len(source_fields) != len(set(source_fields)):
            errors.append(
                "manifest: separately bound action concepts require distinct source fields"
            )


def validate_manifest(manifest: object, *, today: dt.date | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest: root must be a JSON object"]

    if manifest.get("schema_version") != "1.0":
        errors.append("manifest: schema_version must be exactly '1.0'")

    status = manifest.get("status")
    if status not in {"draft", "approved"}:
        errors.append("manifest: status must be exactly 'draft' or 'approved'")
    approved = status == "approved"
    operative = manifest.get("operative")
    if not isinstance(operative, bool):
        errors.append("manifest: operative must be boolean")
    elif status == "draft" and operative:
        errors.append("manifest: draft operative must be false")
    elif approved and not operative:
        errors.append("manifest: approved operative must be true")

    access = manifest.get("access")
    if not isinstance(access, dict):
        errors.append("manifest: access must be an object")
    else:
        if not isinstance(access.get("authenticated_collection"), bool):
            errors.append("manifest: access.authenticated_collection must be boolean")
        if status == "draft":
            if access.get("status") != "pending":
                errors.append("manifest: draft access.status must be exactly 'pending'")
            if access.get("authenticated_collection") is not False:
                errors.append(
                    "manifest: draft access.authenticated_collection must be false"
                )
        elif approved:
            if access.get("status") != "granted":
                errors.append(
                    "manifest: approved access.status must be exactly 'granted'"
                )
            if access.get("authenticated_collection") is not True:
                errors.append(
                    "manifest: approved access.authenticated_collection must be true"
                )

    queries = manifest.get("queries")
    if not isinstance(queries, list):
        errors.append("manifest: queries must be a list")
    elif approved:
        if not queries:
            errors.append("manifest: approved manifests require query identifiers")
        for index, query in enumerate(queries):
            if not isinstance(query, dict):
                errors.append(f"manifest: approved queries[{index}] must be an object")
                continue
            if not _nonempty_string(query.get("id")):
                errors.append(
                    f"manifest: approved queries[{index}].id must be non-empty"
                )
            terms = query.get("terms")
            if not (
                isinstance(terms, list)
                and terms
                and all(_nonempty_string(term) for term in terms)
            ):
                errors.append(
                    f"manifest: approved queries[{index}].terms must be a non-empty list"
                )
            if not isinstance(query.get("facets"), dict):
                errors.append(
                    f"manifest: approved queries[{index}].facets must be an object"
                )
            if not isinstance(query.get("exclusions"), list):
                errors.append(
                    f"manifest: approved queries[{index}].exclusions must be a list"
                )

    _validate_field_semantics(manifest, approved=approved, errors=errors)

    study_interval = manifest.get("study_interval")
    if not isinstance(study_interval, dict):
        errors.append("manifest: study_interval must be an object")
    else:
        interval_operative = study_interval.get("operative")
        if not isinstance(interval_operative, bool):
            errors.append("manifest: study_interval.operative must be boolean")
        elif status == "draft" and interval_operative:
            errors.append("manifest: draft study_interval.operative must be false")
        elif approved and not interval_operative:
            errors.append("manifest: approved study_interval.operative must be true")
        if approved and study_interval.get("date_field_binding_status") != "bound":
            errors.append(
                "manifest: approved study_interval.date_field_binding_status must be 'bound'"
            )
        if approved:
            start = _parse_review_date(study_interval.get("provisional_start"))
            end = _parse_review_date(study_interval.get("provisional_end"))
            if start is None or end is None or start > end:
                errors.append(
                    "manifest: approved study interval must contain ordered ISO dates"
                )

    analysis = manifest.get("analysis")
    if not isinstance(analysis, dict):
        errors.append("manifest: analysis must be an object")
    else:
        comparisons_allowed = analysis.get("comparisons_allowed")
        if not isinstance(comparisons_allowed, bool):
            errors.append("manifest: analysis.comparisons_allowed must be boolean")
        action_comparisons = analysis.get("action_rate_comparisons")
        all_semantics = manifest.get("field_semantics")
        action_semantics = (
            all_semantics.get("action", {}) if isinstance(all_semantics, dict) else {}
        )
        action_enabled = (
            action_semantics.get("comparisons_enabled")
            if isinstance(action_semantics, dict)
            else None
        )
        if not isinstance(action_comparisons, dict):
            errors.append(
                "manifest: analysis.action_rate_comparisons must be an object"
            )
        else:
            action_allowed = action_comparisons.get("allowed")
            if not isinstance(action_allowed, bool):
                errors.append(
                    "manifest: analysis.action_rate_comparisons.allowed must be boolean"
                )
            elif action_allowed != action_enabled:
                errors.append(
                    "manifest: action comparison gates must agree between analysis "
                    "and field semantics"
                )
            if action_allowed and comparisons_allowed is not True:
                errors.append(
                    "manifest: action comparisons require analysis.comparisons_allowed"
                )
            if (
                isinstance(action_allowed, bool)
                and comparisons_allowed != action_allowed
            ):
                errors.append(
                    "manifest: global comparison permission must match the only "
                    "declared comparison category"
                )
            denominator_strata = action_comparisons.get("denominator_strata")
            denominator_set = (
                {
                    value.strip()
                    for value in denominator_strata
                    if isinstance(value, str) and value.strip()
                }
                if isinstance(denominator_strata, list)
                else set()
            )
            if not REQUIRED_DENOMINATOR_STRATA.issubset(denominator_set):
                errors.append(
                    "manifest: action comparisons require provider_or_recipient/"
                    "time_period/notice_type/ecosystem denominator strata"
                )
            for key in (
                "coverage_and_missingness_denominators_required",
                "comparable_reporting_semantics_required",
            ):
                if action_comparisons.get(key) is not True:
                    errors.append(
                        f"manifest: analysis.action_rate_comparisons.{key} must be true"
                    )
            if action_comparisons.get("missing_action_is_no_action") is not False:
                errors.append(
                    "manifest: missing action values must not be treated as no action"
                )
        if status == "draft" and comparisons_allowed is not False:
            errors.append("manifest: draft analysis.comparisons_allowed must be false")

    publication = manifest.get("publication_minimization")
    if not isinstance(publication, dict):
        errors.append("manifest: publication_minimization must be an object")
    else:
        precedence = publication.get("precedence")
        if precedence != "Privacy and data minimization override public auditability":
            errors.append(
                "manifest: publication precedence must put privacy and data "
                "minimization above public auditability"
            )
        if publication.get("unsafe_claim_disposition") != "omit_or_weaken":
            errors.append(
                "manifest: unsafe claims must use disposition 'omit_or_weaken'"
            )
        source_index = publication.get("public_source_index")
        if not isinstance(source_index, dict):
            errors.append(
                "manifest: publication_minimization.public_source_index must be an object"
            )
        else:
            allowed_fields = source_index.get("allowed_fields")
            allowed_set = (
                {
                    value.strip()
                    for value in allowed_fields
                    if isinstance(value, str) and value.strip()
                }
                if isinstance(allowed_fields, list)
                else set()
            )
            if allowed_set != REQUIRED_SOURCE_INDEX_FIELDS:
                errors.append(
                    "manifest: public source index fields must be limited to the "
                    "notice identifier and bounded derived inclusion basis"
                )
            forbidden_content = source_index.get("forbidden_content")
            forbidden_set = (
                {
                    value.strip()
                    for value in forbidden_content
                    if isinstance(value, str) and value.strip()
                }
                if isinstance(forbidden_content, list)
                else set()
            )
            if not REQUIRED_FORBIDDEN_PUBLIC_CONTENT.issubset(forbidden_set):
                errors.append(
                    "manifest: public source index forbidden-content controls are incomplete"
                )
        allowed_binary_artifacts = publication.get("allowed_binary_artifacts")
        if allowed_binary_artifacts != []:
            errors.append(
                "manifest: allowed_binary_artifacts must remain empty; "
                "publish binaries outside Git"
            )

    limits = manifest.get("collection_limits")
    if not isinstance(limits, dict):
        errors.append("manifest: collection_limits must be an object")
    else:
        minimum_delay = limits.get("minimum_seconds_between_requests")
        default_maximum = limits.get("default_maximum_notices_per_run")
        absolute_ceiling = limits.get("absolute_ceiling_notices_per_run")
        if not isinstance(minimum_delay, (int, float)) or minimum_delay < 1:
            errors.append("manifest: collection delay must be at least one second")
        if not isinstance(default_maximum, int) or not 1 <= default_maximum <= 500:
            errors.append(
                "manifest: default maximum notices per run must be between 1 and 500"
            )
        if not isinstance(absolute_ceiling, int) or not 1 <= absolute_ceiling <= 1000:
            errors.append(
                "manifest: absolute ceiling must be between 1 and 1000 notices"
            )
        if (
            isinstance(default_maximum, int)
            and isinstance(absolute_ceiling, int)
            and default_maximum > absolute_ceiling
        ):
            errors.append(
                "manifest: default maximum cannot exceed the absolute ceiling"
            )
        if limits.get("stop_when_ceiling_would_be_exceeded") is not True:
            errors.append(
                "manifest: collection must stop when the ceiling would be exceeded"
            )

    approval = manifest.get("approval")
    if not isinstance(approval, dict):
        errors.append("manifest: approval must be an object")
    elif status == "draft":
        if approval.get("status") != "pending":
            errors.append("manifest: draft approval.status must be exactly 'pending'")
    elif approved:
        if approval.get("status") != "approved":
            errors.append(
                "manifest: approved approval.status must be exactly 'approved'"
            )
        for key in ("approver", "approved_at"):
            if not _nonempty_string(approval.get(key)):
                errors.append(f"manifest: approved approval.{key} must be non-empty")
        if _parse_review_date(approval.get("approved_at")) is None:
            errors.append(
                "manifest: approved approval.approved_at must be an ISO date or timestamp"
            )
        source_commit = approval.get("source_commit")
        if not (
            _nonempty_string(source_commit)
            and re.fullmatch(r"[0-9a-fA-F]{40}", str(source_commit).strip())
        ):
            errors.append(
                "manifest: approved approval.source_commit must be a 40-hex commit"
            )
        digest = approval.get("content_sha256")
        if digest != manifest_content_sha256(manifest):
            errors.append(
                "manifest: approved approval.content_sha256 does not match "
                "canonical manifest content"
            )
        validator = approval.get("validator")
        if not isinstance(validator, dict):
            errors.append("manifest: approved approval.validator must be an object")
        else:
            if validator.get("required") is not True:
                errors.append(
                    "manifest: approved approval.validator.required must be true"
                )
            if validator.get("name") != "query-manifest-validator":
                errors.append(
                    "manifest: approved approval.validator.name must be "
                    "'query-manifest-validator'"
                )
            if validator.get("implementation_status") != "implemented":
                errors.append(
                    "manifest: approved approval.validator.implementation_status "
                    "must be exactly 'implemented'"
                )
            if validator.get("result") != "passed":
                errors.append(
                    "manifest: approved approval.validator.result must be exactly "
                    "'passed'"
                )
            if _parse_review_date(validator.get("validated_at")) is None:
                errors.append(
                    "manifest: approved approval.validator.validated_at must be an "
                    "ISO date or timestamp"
                )

    terms = manifest.get("terms_review")
    if not isinstance(terms, dict):
        errors.append("manifest: terms_review must be an object")
    elif status == "draft":
        if terms.get("status") != "pending":
            errors.append(
                "manifest: draft terms_review.status must be exactly 'pending'"
            )
    elif approved:
        if terms.get("status") != "completed":
            errors.append(
                "manifest: approved terms_review.status must be exactly 'completed'"
            )
        reviewed_at = _parse_review_date(terms.get("reviewed_at"))
        if reviewed_at is None:
            errors.append(
                "manifest: approved terms_review.reviewed_at must be an ISO date"
            )
        else:
            current_date = today or dt.date.today()
            age = (current_date - reviewed_at).days
            if age < 0 or age > TERMS_REVIEW_MAX_AGE_DAYS:
                errors.append(
                    "manifest: approved terms review must be no more than "
                    f"{TERMS_REVIEW_MAX_AGE_DAYS} days old and not future-dated"
                )
        source_url = terms.get("source_url")
        if not (
            _nonempty_string(source_url)
            and urlsplit(str(source_url)).scheme == "https"
            and urlsplit(str(source_url)).hostname == "lumendatabase.org"
        ):
            errors.append(
                "manifest: approved terms_review.source_url must be an official "
                "https://lumendatabase.org URL"
            )
        if not _nonempty_string(terms.get("terms_version")):
            errors.append(
                "manifest: approved terms_review.terms_version must be non-empty"
            )

    implementation = manifest.get("implementation")
    if not isinstance(implementation, dict):
        errors.append("manifest: implementation must be an object")
    elif approved and implementation.get("collector_status") != "implemented":
        errors.append(
            "manifest: approved implementation.collector_status must be 'implemented'"
        )

    return errors


def _validate_required_files(root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: required public artifact is missing")
        elif path.stat().st_size == 0:
            errors.append(f"{relative}: required public artifact is empty")


def _validate_identity(root: Path, public_files: list[Path], errors: list[str]) -> None:
    for relative in (Path("README.md"), Path("CITATION.cff")):
        path = root / relative
        if path.is_file() and LEGAL_NAME not in _read_text(path, errors):
            errors.append(f"{relative}: must use exact legal name {LEGAL_NAME!r}")
    for path in public_files:
        text = _read_text(path, errors)
        if STALE_LEGAL_NAME in text:
            errors.append(
                f"{path.relative_to(root)}: stale affiliation {STALE_LEGAL_NAME!r} "
                "is forbidden"
            )


def _validate_researcher_profile(root: Path, errors: list[str]) -> None:
    path = root / "VERIFICATION.md"
    if not path.is_file():
        return
    text = _read_text(path, errors)
    normalized_text = " ".join(text.split())
    required_markers = {
        "independent researcher": "Jonathan Maye-Hobbs is the independent researcher.",
        "professional affiliation": "JMH Blockchain, LLC is his professional affiliation.",
        "independent study boundary": (
            "The study is independently conducted and has no client or institutional sponsor."
        ),
        "official business validation portal": (
            "https://wyobiz.wyo.gov/Business/ViewCertificate.aspx"
        ),
        "business certificate identifier": "Certificate ID: `104929530`",
    }
    for label, marker in required_markers.items():
        if " ".join(marker.split()) not in normalized_text:
            errors.append(f"VERIFICATION.md: missing {label}")


def _validate_repository_artifacts(root: Path, errors: list[str]) -> None:
    for path in _repository_files(root):
        relative = path.relative_to(root)
        if SENSITIVE_IDENTITY_FILENAME_RE.search(relative.name):
            errors.append(
                f"{relative}: private identity-evidence filename is forbidden"
            )
        if (
            path.suffix.lower() not in PUBLIC_SUFFIXES
            and path.name not in ALLOWED_EXTENSIONLESS_FILES
        ):
            errors.append(
                f"{relative}: unsupported repository artifact; "
                "Git history must remain text-only"
            )
            continue
        if relative not in IDENTITY_CONTROL_FILES:
            text = _read_text(path, errors)
            if SENSITIVE_IDENTITY_CONTENT_RE.search(text):
                errors.append(
                    f"{relative}: private identity-evidence content is forbidden"
                )


def _validate_source_commit(root: Path, manifest: object, errors: list[str]) -> None:
    if not isinstance(manifest, dict) or manifest.get("status") != "approved":
        return
    approval = manifest.get("approval")
    source_commit = (
        approval.get("source_commit") if isinstance(approval, dict) else None
    )
    if not (
        _nonempty_string(source_commit)
        and re.fullmatch(r"[0-9a-fA-F]{40}", str(source_commit).strip())
    ):
        return
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "cat-file",
            "-e",
            f"{str(source_commit).strip()}^{{commit}}",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        errors.append(
            "manifest: approved approval.source_commit must exist in repository history"
        )


def _validate_disclosure(root: Path, errors: list[str]) -> None:
    occurrences = 0
    for path in sorted(root.rglob("*.md")):
        if EXCLUDED_PARTS.intersection(path.relative_to(root).parts):
            continue
        lines = _read_text(path, errors).splitlines()
        for index, line in enumerate(lines):
            if LUMEN_DISCLOSURE not in line:
                continue
            occurrences += 1
            prior = " ".join(lines[max(0, index - 4) : index]).lower()
            if not line.lstrip().startswith("> "):
                errors.append(
                    f"{path.relative_to(root)}:{index + 1}: Lumen disclosure must "
                    "be a quoted future-report template, not a present-use claim"
                )
            if not any(
                marker in prior for marker in ("will include", "future", "planned")
            ):
                errors.append(
                    f"{path.relative_to(root)}:{index + 1}: Lumen disclosure needs "
                    "explicit future-publication context"
                )
    if occurrences == 0:
        errors.append("repository: exact required future Lumen disclosure is missing")


def _validate_local_links(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*.md")):
        if EXCLUDED_PARTS.intersection(path.relative_to(root).parts):
            continue
        text = _read_text(path, errors)
        for raw_target in LOCAL_LINK_RE.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split(maxsplit=1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(("#", "//")):
                continue
            relative_target = unquote(parsed.path)
            if not relative_target:
                continue
            resolved = (path.parent / relative_target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(
                    f"{path.relative_to(root)}: local link escapes repository: {target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(root)}: broken local link target: {target}"
                )


def _validate_public_secrets(
    root: Path, public_files: list[Path], errors: list[str]
) -> None:
    for path in public_files:
        text = _read_text(path, errors)
        relative = path.relative_to(root)
        if EIN_RE.search(text):
            errors.append(f"{relative}: public file contains an EIN-shaped value")
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{relative}: public file contains an obvious {label}")


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    _validate_required_files(root, errors)
    public_files = _public_files(root)
    _validate_identity(root, public_files, errors)
    _validate_researcher_profile(root, errors)
    _validate_disclosure(root, errors)
    _validate_local_links(root, errors)
    _validate_public_secrets(root, public_files, errors)

    manifest_path = root / MANIFEST_PATH
    manifest: object = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{MANIFEST_PATH}: invalid JSON: {exc}")
        else:
            errors.extend(validate_manifest(manifest))
            _validate_source_commit(root, manifest, errors)
    _validate_repository_artifacts(root, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the validator's parent repository)",
    )
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

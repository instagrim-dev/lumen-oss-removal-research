from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPOSITORY_ROOT / "scripts" / "validate_repository.py"
SPEC = importlib.util.spec_from_file_location("validate_repository", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def draft_manifest() -> dict[str, object]:
    return json.loads(
        (REPOSITORY_ROOT / validator.MANIFEST_PATH).read_text(encoding="utf-8")
    )


def approved_manifest() -> dict[str, object]:
    manifest = draft_manifest()
    manifest["status"] = "approved"
    manifest["operative"] = True
    manifest["access"] = {
        "status": "granted",
        "authenticated_collection": True,
    }
    manifest["queries"] = [
        {
            "id": "source-host-example",
            "terms": ["example.org"],
            "facets": {},
            "exclusions": [],
        }
    ]
    study_interval = manifest["study_interval"]
    assert isinstance(study_interval, dict)
    study_interval["operative"] = True
    study_interval["date_field_binding_status"] = "bound"
    semantics = manifest["field_semantics"]
    assert isinstance(semantics, dict)
    semantics["date"] = {
        "status": "bound",
        "source_field": "date_received",
        "definition": "UTC date on which the Lumen record says it was received.",
        "describes": "Lumen receipt of the represented notice",
        "timezone": "UTC",
        "start_inclusive": True,
        "end_inclusive": True,
        "missing_date_handling": "exclude and report",
    }
    for name in validator.REQUIRED_FIELD_SEMANTICS:
        semantics[name] = {
            "status": "bound",
            "source_field": f"source_{name}",
            "definition": f"Bound definition for {name}.",
            "missing_value_handling": "retain as missing and report coverage",
        }
    for name in ("jurisdiction", "country"):
        entry = semantics[name]
        assert isinstance(entry, dict)
        entry["describes_party_notice_authority_or_record"] = "represented notice"
    semantics["action"] = {
        "status": "bound",
        "reported_or_requested_action": {
            "source_field": "reported_action",
            "definition": "Action reported or requested in the represented record.",
            "source_owner": "represented notice",
            "missing_value_handling": "retain as missing",
        },
        "action_actually_taken": {
            "source_field": "action_taken",
            "definition": "Action actually taken as reported by the responsible actor.",
            "source_owner": "responsible recipient",
            "missing_value_handling": "retain as missing",
        },
        "lumen_record_state": {
            "source_field": "record_state",
            "definition": "State of the Lumen record.",
            "source_owner": "Lumen",
            "missing_value_handling": "retain as missing",
        },
        "missingness_breakdowns": sorted(validator.REQUIRED_ACTION_BREAKDOWNS),
        "coverage_rule": "Publish a coverage denominator beside every comparison.",
        "comparison_basis": None,
        "comparisons_enabled": False,
    }
    analysis = manifest["analysis"]
    assert isinstance(analysis, dict)
    analysis["comparisons_allowed"] = False
    action_comparisons = analysis["action_rate_comparisons"]
    assert isinstance(action_comparisons, dict)
    action_comparisons["allowed"] = False
    manifest["terms_review"] = {
        "status": "completed",
        "reviewed_at": dt.date.today().isoformat(),
        "source_url": "https://lumendatabase.org/pages/license",
        "terms_version": "reviewed-current-page",
    }
    manifest["approval"] = {
        "status": "approved",
        "approver": "Jonathan Maye-Hobbs",
        "approved_at": dt.date.today().isoformat(),
        "source_commit": "a" * 40,
        "content_sha256": None,
        "validator": {
            "required": True,
            "name": "query-manifest-validator",
            "implementation_status": "implemented",
            "result": "passed",
            "validated_at": dt.date.today().isoformat(),
        },
    }
    implementation = manifest["implementation"]
    assert isinstance(implementation, dict)
    implementation["collector_status"] = "implemented"
    manifest["approval"]["content_sha256"] = validator.manifest_content_sha256(manifest)
    return manifest


class RepositoryValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self._write_repository(draft_manifest())

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_repository(self, manifest: dict[str, object]) -> None:
        self._write(
            "README.md",
            "# Research\n\n"
            "Protocol draft; Lumen researcher access is pending. "
            "Data collection has not begun.\n\n"
            "Jonathan Maye-Hobbs works through JMH Blockchain, LLC.\n\n"
            "See [the protocol](RESEARCH_PROTOCOL.md).\n",
        )
        self._write(
            "RESEARCH_PROTOCOL.md",
            "# Protocol\n\nThe future report will include this disclosure:\n\n"
            "> This product uses the Lumen API but is not endorsed or certified "
            "by Lumen.\n",
        )
        self._write("DATA_HANDLING.md", "# Data handling\n")
        self._write("PUBLICATION_PLAN.md", "# Publication plan\n")
        self._write(
            "CITATION.cff",
            'cff-version: 1.2.0\naffiliation: "JMH Blockchain, LLC"\n',
        )
        self._write("LICENSE.md", "# CC BY 4.0\n")
        self._write("data/README.md", "# Data\n")
        self._write("reports/README.md", "# Reports\n")
        self._write("manifests/README.md", "# Query manifests\n")
        self._write(
            "VERIFICATION.md",
            "# Verification\n\n"
            "Jonathan Maye-Hobbs is the independent researcher.\n\n"
            "JMH Blockchain, LLC is his professional affiliation.\n\n"
            "The study is independently conducted and has no client or "
            "institutional sponsor.\n\n"
            "https://wyobiz.wyo.gov/Business/ViewCertificate.aspx\n\n"
            "Certificate ID: `104929530`\n",
        )
        self._write(
            str(validator.MANIFEST_PATH),
            json.dumps(manifest, indent=2) + "\n",
        )

    def _errors(self) -> list[str]:
        return validator.validate_repository(self.root)

    def test_passing_repository(self) -> None:
        self.assertEqual([], self._errors())

    def test_stale_affiliation_regression(self) -> None:
        stale = "JMH" + ", LLC"
        self._write("README.md", f"# Research\n\nAffiliation: {stale}\n")
        errors = self._errors()
        self.assertTrue(any("exact legal name" in error for error in errors))
        self.assertTrue(any("stale affiliation" in error for error in errors))

    def test_ein_and_secret_boundary(self) -> None:
        ein = "12" + "-" + "3456789"
        token = "sk-" + "A" * 24
        self._write("PUBLICATION_PLAN.md", f"EIN {ein}\nToken {token}\n")
        errors = self._errors()
        self.assertTrue(any("EIN-shaped" in error for error in errors))
        self.assertTrue(any("OpenAI-style token" in error for error in errors))

    def test_invalid_approved_manifest(self) -> None:
        manifest = approved_manifest()
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["approver"] = None
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        self._write_repository(manifest)
        errors = self._errors()
        self.assertTrue(any("approval.approver" in error for error in errors))

    def test_approved_manifest_requires_granted_access(self) -> None:
        manifest = approved_manifest()
        access = manifest["access"]
        assert isinstance(access, dict)
        access["authenticated_collection"] = False
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("authenticated_collection" in error for error in errors))

    def test_approved_manifest_requires_passing_validator_record(self) -> None:
        manifest = approved_manifest()
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        validator_record = approval["validator"]
        assert isinstance(validator_record, dict)
        validator_record["result"] = "not_run"
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("validator.result" in error for error in errors))

    def test_approved_manifest_requires_validator_identity(self) -> None:
        manifest = approved_manifest()
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        validator_record = approval["validator"]
        assert isinstance(validator_record, dict)
        del validator_record["required"]
        del validator_record["name"]
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("validator.required" in error for error in errors))
        self.assertTrue(any("validator.name" in error for error in errors))

    def test_approved_manifest_cannot_remain_nonoperative(self) -> None:
        manifest = approved_manifest()
        manifest["operative"] = False
        study_interval = manifest["study_interval"]
        assert isinstance(study_interval, dict)
        study_interval["operative"] = False
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["status"] = "pending"
        terms = manifest["terms_review"]
        assert isinstance(terms, dict)
        terms["status"] = "pending"
        implementation = manifest["implementation"]
        assert isinstance(implementation, dict)
        implementation["collector_status"] = "future"
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(
            any("approved operative must be true" in error for error in errors)
        )
        self.assertTrue(any("study_interval.operative" in error for error in errors))
        self.assertTrue(any("approval.status" in error for error in errors))
        self.assertTrue(any("terms_review.status" in error for error in errors))
        self.assertTrue(any("collector_status" in error for error in errors))

    def test_privacy_and_comparison_gates_cannot_be_weakened(self) -> None:
        manifest = approved_manifest()
        publication = manifest["publication_minimization"]
        assert isinstance(publication, dict)
        publication["precedence"] = "Public auditability overrides privacy"
        publication["allowed_binary_artifacts"] = ["reports/appendix.pdf"]
        source_index = publication["public_source_index"]
        assert isinstance(source_index, dict)
        source_index["allowed_fields"] = ["lumen_notice_id", "raw_urls"]
        analysis = manifest["analysis"]
        assert isinstance(analysis, dict)
        action_comparisons = analysis["action_rate_comparisons"]
        assert isinstance(action_comparisons, dict)
        action_comparisons["missing_action_is_no_action"] = True
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("publication precedence" in error for error in errors))
        self.assertTrue(any("allowed_binary_artifacts" in error for error in errors))
        self.assertTrue(any("source index fields" in error for error in errors))
        self.assertTrue(
            any("must not be treated as no action" in error for error in errors)
        )

    def test_action_and_planned_fields_require_separate_bindings(self) -> None:
        manifest = approved_manifest()
        semantics = manifest["field_semantics"]
        assert isinstance(semantics, dict)
        action = semantics["action"]
        assert isinstance(action, dict)
        del action["action_actually_taken"]
        del semantics["ecosystem"]
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(
            any("action.action_actually_taken" in error for error in errors)
        )
        self.assertTrue(any("field_semantics.ecosystem" in error for error in errors))

    def test_action_bindings_require_distinct_source_fields(self) -> None:
        manifest = approved_manifest()
        semantics = manifest["field_semantics"]
        assert isinstance(semantics, dict)
        action = semantics["action"]
        assert isinstance(action, dict)
        for name in validator.REQUIRED_ACTION_BINDINGS:
            binding = action[name]
            assert isinstance(binding, dict)
            binding["source_field"] = "conflated_action_field"
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        errors = validator.validate_manifest(manifest)
        self.assertTrue(any("distinct source fields" in error for error in errors))

    def test_approved_source_commit_must_exist(self) -> None:
        self._write_repository(approved_manifest())
        errors = self._errors()
        self.assertTrue(
            any("must exist in repository history" in error for error in errors)
        )

    def test_private_identity_binary_is_rejected(self) -> None:
        path = self.root / "JMH Blockchain LLC CP575.pdf"
        path.write_bytes(b"%PDF-1.4 synthetic private identity evidence")
        errors = self._errors()
        self.assertTrue(
            any("private identity-evidence filename" in error for error in errors)
        )
        self.assertTrue(
            any("Git history must remain text-only" in error for error in errors)
        )

    def test_disguised_binary_artifact_is_rejected(self) -> None:
        path = self.root / "identity.bin"
        path.write_bytes(b"IRS CP 575 " + b"12" + b"-" + b"3456789")
        errors = self._errors()
        self.assertTrue(
            any("identity.bin" in error and "text-only" in error for error in errors)
        )

    def test_report_pdf_cannot_be_allowlisted_into_git(self) -> None:
        manifest = approved_manifest()
        publication = manifest["publication_minimization"]
        assert isinstance(publication, dict)
        publication["allowed_binary_artifacts"] = ["reports/appendix.pdf"]
        approval = manifest["approval"]
        assert isinstance(approval, dict)
        approval["content_sha256"] = validator.manifest_content_sha256(manifest)
        self._write_repository(manifest)
        path = self.root / "reports" / "appendix.pdf"
        path.write_bytes(b"%PDF-1.4 synthetic report payload")
        errors = self._errors()
        self.assertTrue(any("allowed_binary_artifacts" in error for error in errors))
        self.assertTrue(
            any(
                "reports/appendix.pdf" in error and "text-only" in error
                for error in errors
            )
        )

    def test_researcher_profile_is_required(self) -> None:
        self._write(
            "VERIFICATION.md",
            "# Verification\n\nJonathan Maye-Hobbs is the independent researcher.\n",
        )
        errors = self._errors()
        self.assertTrue(any("professional affiliation" in error for error in errors))
        self.assertTrue(any("independent study boundary" in error for error in errors))

    def test_approved_manifest_with_complete_controls(self) -> None:
        manifest = approved_manifest()
        self.assertEqual([], validator.validate_manifest(manifest))

    def test_action_comparison_gate(self) -> None:
        manifest = copy.deepcopy(draft_manifest())
        semantics = manifest["field_semantics"]
        assert isinstance(semantics, dict)
        action = semantics["action"]
        assert isinstance(action, dict)
        action["comparisons_enabled"] = True
        self._write_repository(manifest)
        errors = self._errors()
        self.assertTrue(any("action comparisons require" in error for error in errors))

    def test_broken_local_link(self) -> None:
        self._write(
            "README.md",
            "# Research\n\n"
            "Protocol draft; Lumen researcher access is pending. "
            "Data collection has not begun.\n\n"
            "JMH Blockchain, LLC\n\n"
            "See [missing](does-not-exist.md).\n",
        )
        errors = self._errors()
        self.assertTrue(any("broken local link" in error for error in errors))

    def test_unquoted_disclosure_cannot_claim_present_api_use(self) -> None:
        self._write(
            "RESEARCH_PROTOCOL.md",
            "# Protocol\n\n"
            "This product uses the Lumen API but is not endorsed or certified "
            "by Lumen.\n",
        )
        errors = self._errors()
        self.assertTrue(
            any("quoted future-report template" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()

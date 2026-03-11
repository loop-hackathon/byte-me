"""
Unit tests for services/security_service.py

All Docker and git subprocess calls are mocked — no real network or Docker needed.
Run from the backend/ directory with:
    python -m pytest tests/test_security_service.py -v
"""

import json
import subprocess
import unittest
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from services.security_service import (
    calculate_security_risk_score,
    parse_trivy_results,
    run_trivy_scan,
    scan_repository,
)


# ---------------------------------------------------------------------------
# Sample Trivy JSON payloads
# ---------------------------------------------------------------------------

SAMPLE_TRIVY_JSON = json.dumps({
    "SchemaVersion": 2,
    "ArtifactName": "/project",
    "ArtifactType": "filesystem",
    "Results": [
        {
            "Target": "requirements.txt",
            "Class": "lang-pkgs",
            "Type": "pip",
            "Vulnerabilities": [
                {"VulnerabilityID": "CVE-2023-0001", "Severity": "CRITICAL"},
                {"VulnerabilityID": "CVE-2023-0002", "Severity": "CRITICAL"},
                {"VulnerabilityID": "CVE-2023-0003", "Severity": "HIGH"},
                {"VulnerabilityID": "CVE-2023-0004", "Severity": "HIGH"},
                {"VulnerabilityID": "CVE-2023-0005", "Severity": "HIGH"},
                {"VulnerabilityID": "CVE-2023-0006", "Severity": "MEDIUM"},
                {"VulnerabilityID": "CVE-2023-0007", "Severity": "LOW"},
            ],
        },
        {
            "Target": "package.json",
            "Class": "lang-pkgs",
            "Type": "npm",
            "Vulnerabilities": [
                {"VulnerabilityID": "CVE-2023-0008", "Severity": "HIGH"},
                {"VulnerabilityID": "CVE-2023-0009", "Severity": "HIGH"},
                {"VulnerabilityID": "CVE-2023-0010", "Severity": "MEDIUM"},
                {"VulnerabilityID": "CVE-2023-0011", "Severity": "MEDIUM"},
                {"VulnerabilityID": "CVE-2023-0012", "Severity": "LOW"},
                {"VulnerabilityID": "CVE-2023-0013", "Severity": "LOW"},
            ],
        },
    ],
})

EMPTY_TRIVY_JSON = json.dumps({
    "SchemaVersion": 2,
    "Results": [],
})

NO_VULNS_TRIVY_JSON = json.dumps({
    "SchemaVersion": 2,
    "Results": [
        {
            "Target": "go.sum",
            "Class": "lang-pkgs",
            "Type": "gomod",
            "Vulnerabilities": None,   # Trivy sometimes returns null
        }
    ],
})

PATCH_BASE = "services.security_service"


# ---------------------------------------------------------------------------
# parse_trivy_results
# ---------------------------------------------------------------------------

class TestParseTrivyResults:

    def test_happy_path(self):
        counts = parse_trivy_results(SAMPLE_TRIVY_JSON)
        assert counts["critical"] == 2
        assert counts["high"] == 5       # 3 + 2
        assert counts["medium"] == 3     # 1 + 2
        assert counts["low"] == 3        # 1 + 2

    def test_empty_results(self):
        counts = parse_trivy_results(EMPTY_TRIVY_JSON)
        assert counts == {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}

    def test_null_vulnerabilities_field(self):
        """Trivy sometimes emits Vulnerabilities: null — should not crash."""
        counts = parse_trivy_results(NO_VULNS_TRIVY_JSON)
        assert counts["critical"] == 0
        assert counts["high"] == 0

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Failed to parse Trivy JSON"):
            parse_trivy_results("not-json-at-all")

    def test_unknown_severity_counted(self):
        data = json.dumps({
            "Results": [{
                "Vulnerabilities": [
                    {"Severity": "WEIRD_CUSTOM"},
                ]
            }]
        })
        counts = parse_trivy_results(data)
        assert counts["unknown"] == 1
        assert counts["critical"] == 0


# ---------------------------------------------------------------------------
# calculate_security_risk_score
# ---------------------------------------------------------------------------

class TestCalculateSecurityRiskScore:

    def test_all_zeros(self):
        assert calculate_security_risk_score(
            {"critical": 0, "high": 0, "medium": 0, "low": 0}
        ) == 0.0

    def test_capped_at_100(self):
        # 2*25 + 5*10 + 7*3 + 3*1 = 50+50+21+3 = 124 → capped
        metrics = {"critical": 2, "high": 5, "medium": 7, "low": 3}
        assert calculate_security_risk_score(metrics) == 100.0

    def test_not_capped(self):
        # 0*25 + 1*10 + 2*3 + 1*1 = 17
        metrics = {"critical": 0, "high": 1, "medium": 2, "low": 1}
        assert calculate_security_risk_score(metrics) == 17.0

    def test_large_numbers_capped(self):
        metrics = {"critical": 100, "high": 100, "medium": 100, "low": 100}
        assert calculate_security_risk_score(metrics) == 100.0

    def test_only_criticals(self):
        # 4*25 = 100
        metrics = {"critical": 4, "high": 0, "medium": 0, "low": 0}
        assert calculate_security_risk_score(metrics) == 100.0

    def test_single_critical(self):
        # 1*25 = 25
        metrics = {"critical": 1, "high": 0, "medium": 0, "low": 0}
        assert calculate_security_risk_score(metrics) == 25.0


# ---------------------------------------------------------------------------
# run_trivy_scan
# ---------------------------------------------------------------------------

class TestRunTrivyScan:

    def _make_proc(self, returncode: int, stdout: str, stderr: str = "") -> MagicMock:
        proc = MagicMock()
        proc.returncode = returncode
        proc.stdout = stdout
        proc.stderr = stderr
        return proc

    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = self._make_proc(0, SAMPLE_TRIVY_JSON)
        result = run_trivy_scan("/tmp/fake_repo")
        assert result == SAMPLE_TRIVY_JSON
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "aquasec/trivy" in cmd

    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_nonzero_exit_raises(self, mock_run):
        mock_run.return_value = self._make_proc(1, "", "docker not found")
        with pytest.raises(RuntimeError, match="Trivy / Docker exited"):
            run_trivy_scan("/tmp/fake_repo")

    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_empty_output_raises(self, mock_run):
        mock_run.return_value = self._make_proc(0, "   ")
        with pytest.raises(RuntimeError, match="no output"):
            run_trivy_scan("/tmp/fake_repo")

    @patch(f"{PATCH_BASE}.subprocess.run", side_effect=FileNotFoundError("docker"))
    def test_docker_not_found_raises(self, _mock_run):
        with pytest.raises(FileNotFoundError, match="Docker executable not found"):
            run_trivy_scan("/tmp/fake_repo")

    @patch(
        f"{PATCH_BASE}.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=300),
    )
    def test_timeout_raises(self, _mock_run):
        with pytest.raises(RuntimeError, match="timed out"):
            run_trivy_scan("/tmp/fake_repo")


# ---------------------------------------------------------------------------
# scan_repository (integration-level, all subprocesses mocked)
# ---------------------------------------------------------------------------

class TestScanRepository:

    def _ok_proc(self):
        proc = MagicMock()
        proc.returncode = 0
        proc.stderr = ""
        return proc

    def _fail_proc(self):
        proc = MagicMock()
        proc.returncode = 128
        proc.stderr = "fatal: repository not found"
        return proc

    @patch(f"{PATCH_BASE}.shutil.rmtree")
    @patch(f"{PATCH_BASE}.run_trivy_scan")
    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_full_flow_success(self, mock_subprocess, mock_trivy, mock_rmtree):
        mock_subprocess.return_value = self._ok_proc()
        mock_trivy.return_value = SAMPLE_TRIVY_JSON

        result = scan_repository("octocat/Hello-World", token=None, ref="abc1234")

        assert result is not None
        assert "risk_score" in result
        assert result["security_metrics"]["critical"] == 2
        assert result["security_metrics"]["high"] == 5
        assert result["risk_score"] == 100.0   # capped

    @patch(f"{PATCH_BASE}.shutil.rmtree")
    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_clone_failure_returns_none(self, mock_subprocess, mock_rmtree):
        mock_subprocess.return_value = self._fail_proc()
        result = scan_repository("octocat/private-repo")
        assert result is None

    @patch(f"{PATCH_BASE}.shutil.rmtree")
    @patch(f"{PATCH_BASE}.run_trivy_scan", side_effect=RuntimeError("Docker not running"))
    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_trivy_failure_returns_none(self, mock_subprocess, _mock_trivy, mock_rmtree):
        mock_subprocess.return_value = self._ok_proc()
        result = scan_repository("octocat/Hello-World")
        assert result is None

    @patch(f"{PATCH_BASE}.shutil.rmtree")
    @patch(f"{PATCH_BASE}.run_trivy_scan")
    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_uses_token_in_clone_url(self, mock_subprocess, mock_trivy, mock_rmtree):
        mock_subprocess.return_value = self._ok_proc()
        mock_trivy.return_value = EMPTY_TRIVY_JSON

        scan_repository("owner/repo", token="ghp_secret", ref=None)

        # First call to subprocess.run is the git clone
        clone_cmd = mock_subprocess.call_args_list[0][0][0]
        assert "ghp_secret@github.com" in " ".join(clone_cmd)

    @patch(f"{PATCH_BASE}.shutil.rmtree")
    @patch(f"{PATCH_BASE}.subprocess.run", side_effect=FileNotFoundError("git"))
    def test_git_not_found_returns_none(self, _mock_run, mock_rmtree):
        result = scan_repository("octocat/Hello-World")
        assert result is None

    @patch(f"{PATCH_BASE}.shutil.rmtree")
    @patch(f"{PATCH_BASE}.run_trivy_scan")
    @patch(f"{PATCH_BASE}.subprocess.run")
    def test_zero_vulnerabilities(self, mock_subprocess, mock_trivy, mock_rmtree):
        mock_subprocess.return_value = self._ok_proc()
        mock_trivy.return_value = EMPTY_TRIVY_JSON

        result = scan_repository("octocat/clean-repo")

        assert result is not None
        assert result["risk_score"] == 0.0
        assert result["security_metrics"]["critical"] == 0

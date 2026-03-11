"""
Security service for running Trivy vulnerability scans on repository releases.

Flow:
    scan_repository()
        → git clone into temp dir
        → run_trivy_scan()  (docker run aquasec/trivy)
        → parse_trivy_results()
        → calculate_security_risk_score()
        → cleanup temp dir
        → return SecurityScanResult dict
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type alias for the vulnerability count dict
# ---------------------------------------------------------------------------
VulnCounts = Dict[str, int]   # keys: critical, high, medium, low, unknown


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def run_trivy_scan(repo_path: str) -> str:
    """
    Run a Trivy filesystem scan on *repo_path* using Docker.

    Command executed:
        docker run --rm -v <repo_path>:/project aquasec/trivy fs /project -f json

    Args:
        repo_path: Absolute path to the local repository directory.

    Returns:
        Raw JSON string produced by Trivy.

    Raises:
        FileNotFoundError: If Docker is not found in PATH.
        RuntimeError: If Docker exits with a non-zero code,
                      or if Trivy output cannot be decoded.
    """
    # Normalise path for Docker volume mount (Windows → forward slashes)
    if sys.platform.startswith("win"):
        # Docker Desktop on Windows expects paths like C:/Users/...
        normalised = repo_path.replace("\\", "/")
    else:
        normalised = repo_path

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{normalised}:/project",
        "aquasec/trivy",
        "fs", "/project",
        "-f", "json",
        "--exit-code", "0",   # never fail just because vulns were found
        "--quiet",             # suppress progress output
    ]

    logger.info("Running Trivy scan: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,   # 5-minute ceiling
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Docker executable not found. "
            "Make sure Docker Desktop is installed and running."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Trivy scan timed out after 300 seconds.") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"Trivy / Docker exited with code {result.returncode}. "
            f"stderr: {result.stderr[:500]}"
        )

    if not result.stdout.strip():
        raise RuntimeError("Trivy produced no output — possible Docker issue.")

    return result.stdout


def parse_trivy_results(raw_json: str) -> VulnCounts:
    """
    Parse Trivy's JSON output and aggregate vulnerability counts by severity.

    Trivy JSON structure (abbreviated):
    {
        "Results": [
            {
                "Vulnerabilities": [
                    {"Severity": "CRITICAL", ...},
                    {"Severity": "HIGH", ...},
                    ...
                ]
            }
        ]
    }

    Args:
        raw_json: JSON string from Trivy.

    Returns:
        Dict with keys: critical, high, medium, low, unknown.

    Raises:
        ValueError: If the JSON cannot be parsed.
    """
    counts: VulnCounts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "unknown": 0,
    }

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse Trivy JSON output: {exc}") from exc

    results = data.get("Results") or []
    for result_block in results:
        vulnerabilities = result_block.get("Vulnerabilities") or []
        for vuln in vulnerabilities:
            severity = vuln.get("Severity", "UNKNOWN").lower()
            if severity in counts:
                counts[severity] += 1
            else:
                counts["unknown"] += 1

    logger.info(
        "Trivy parsed: critical=%d high=%d medium=%d low=%d unknown=%d",
        counts["critical"], counts["high"], counts["medium"],
        counts["low"], counts["unknown"],
    )
    return counts


def calculate_security_risk_score(metrics: VulnCounts) -> float:
    """
    Convert vulnerability counts into a 0–100 risk score.

    Weights:
        critical : 25 pts each
        high     : 10 pts each
        medium   :  3 pts each
        low      :  1 pt  each

    The raw score is capped at 100.

    Args:
        metrics: Dict returned by :func:`parse_trivy_results`.

    Returns:
        Float in [0.0, 100.0].
    """
    raw = (
        metrics.get("critical", 0) * 25
        + metrics.get("high", 0) * 10
        + metrics.get("medium", 0) * 3
        + metrics.get("low", 0) * 1
    )
    score = min(float(raw), 100.0)
    logger.info("Security risk score: %.1f", score)
    return score


def scan_repository(
    repo_full_name: str,
    token: Optional[str] = None,
    ref: Optional[str] = None,
) -> Optional[Dict]:
    """
    Orchestrate a full security scan of a GitHub repository.

    Steps:
        1. Create a temporary directory.
        2. Clone the repo (shallow, at *ref* if provided).
        3. Run :func:`run_trivy_scan`.
        4. Parse results and compute score.
        5. Delete the temporary directory.

    Args:
        repo_full_name: GitHub "owner/repo" string (e.g. "octocat/Hello-World").
        token: Optional GitHub personal-access token (for private repos).
        ref: Optional git ref / commit SHA to check out.
             Ignored when the repo has no matching branch for that ref;
             in that case the default branch is used.

    Returns:
        A dict::

            {
                "risk_score": <float 0-100>,
                "security_metrics": {
                    "critical": <int>,
                    "high": <int>,
                    "medium": <int>,
                    "low": <int>,
                    "unknown": <int>,
                },
            }

        Returns ``None`` if any step fails (non-raising — callers should
        treat ``None`` as a scan failure without aborting the request).
    """
    tmp_dir: Optional[str] = None
    try:
        # ------------------------------------------------------------------
        # Build clone URL (supports public and private repos)
        # ------------------------------------------------------------------
        if token:
            clone_url = f"https://{token}@github.com/{repo_full_name}.git"
        else:
            clone_url = f"https://github.com/{repo_full_name}.git"

        # ------------------------------------------------------------------
        # Create temp directory and clone
        # ------------------------------------------------------------------
        tmp_dir = tempfile.mkdtemp(prefix="cloudhelm_scan_")
        repo_dir = os.path.join(tmp_dir, "repo")

        logger.info("Cloning %s into %s", repo_full_name, repo_dir)

        clone_cmd = [
            "git", "clone",
            "--depth", "1",     # shallow — speeds things up
            clone_url,
            repo_dir,
        ]

        # If a specific ref was given, try to clone that branch/tag directly.
        # For a commit SHA we have to do a post-clone checkout (below).
        clone_result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if clone_result.returncode != 0:
            logger.warning(
                "git clone failed (rc=%d): %s",
                clone_result.returncode,
                clone_result.stderr[:500],
            )
            return None

        # Optional: checkout a specific commit if ref looks like a SHA
        if ref and len(ref) >= 7:
            checkout_result = subprocess.run(
                ["git", "-C", repo_dir, "checkout", ref],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if checkout_result.returncode != 0:
                logger.debug(
                    "Could not checkout ref %s (may be a short SHA or tag) — "
                    "scanning default branch instead. stderr: %s",
                    ref, checkout_result.stderr[:200],
                )

        # ------------------------------------------------------------------
        # Run Trivy scan
        # ------------------------------------------------------------------
        raw_json = run_trivy_scan(repo_dir)

        # ------------------------------------------------------------------
        # Parse and score
        # ------------------------------------------------------------------
        metrics = parse_trivy_results(raw_json)
        score = calculate_security_risk_score(metrics)

        return {
            "risk_score": score,
            "security_metrics": {
                "critical": metrics["critical"],
                "high": metrics["high"],
                "medium": metrics["medium"],
                "low": metrics["low"],
                "unknown": metrics.get("unknown", 0),
            },
        }

    except FileNotFoundError as exc:
        logger.error("scan_repository: tool not found — %s", exc)
        return None
    except RuntimeError as exc:
        logger.error("scan_repository: runtime error — %s", exc)
        return None
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("scan_repository: unexpected error — %s", exc)
        return None
    finally:
        # Always clean up the temp directory
        if tmp_dir and os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
                logger.debug("Cleaned up temp dir: %s", tmp_dir)
            except Exception as cleanup_exc:  # pylint: disable=broad-except
                logger.warning("Could not remove temp dir %s: %s", tmp_dir, cleanup_exc)

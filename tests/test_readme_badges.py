from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_badges_match_release_facts() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads(
        (ROOT / "assets/protocol_assets/system/graph_population/v001/manifest.json").read_text(
            encoding="utf-8"
        )
    )
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    project = pyproject["project"]
    version = project["version"]
    python_requirement = project["requires-python"].removeprefix(">=")
    protocol_version = manifest["version"]

    assert f"badge/version-{version}-blue" in readme
    assert f"badge/python-{python_requirement}%2B-blue" in readme
    assert "MIT License" in license_text
    assert "badge/license-MIT-green" in readme
    assert f"badge/graph_population_protocol-{protocol_version}-purple" in readme


def test_readme_ci_badge_points_to_existing_workflow() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    workflow = ROOT / ".github/workflows/ci.yml"

    assert workflow.exists()
    assert "actions/workflows/ci.yml/badge.svg" in readme
    assert "actions/workflows/ci.yml" in readme

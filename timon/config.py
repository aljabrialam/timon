"""Config loading. Configs live in config/*.yaml and are versioned in git."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def load(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    path = (config_dir or CONFIG_DIR) / f"{name}.yaml"
    with path.open() as f:
        return yaml.safe_load(f) or {}


def limits(config_dir: Path | None = None) -> dict[str, Any]:
    return load("risk_limits", config_dir)


def calendar(config_dir: Path | None = None) -> dict[str, Any]:
    return load("calendar", config_dir)


def account(config_dir: Path | None = None) -> dict[str, Any]:
    return load("account", config_dir)

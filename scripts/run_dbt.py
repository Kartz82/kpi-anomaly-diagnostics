"""Convenience wrapper for running:

- dbt debug
- dbt run
- dbt test
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT_DIR / "dbt"


def _ensure_dbt_available() -> str:
    executable = shutil.which("dbt")
    if not executable:
        raise SystemExit(
            "dbt is not installed or not on PATH. Install requirements from requirements.txt "
            "before running the dbt project."
        )
    return executable


def _ensure_profiles_dir(env: dict[str, str]) -> None:
    if "DBT_PROFILES_DIR" not in env:
        if (DBT_DIR / "profiles.yml").exists():
            env["DBT_PROFILES_DIR"] = str(DBT_DIR)
        else:
            raise SystemExit(
                "dbt/profiles.yml is missing. Copy dbt/profiles.example.yml to dbt/profiles.yml "
                "or set DBT_PROFILES_DIR to a directory containing profiles.yml."
            )


def _run(command: list[str], env: dict[str, str]) -> None:
    print("$", " ".join(command))
    try:
        subprocess.run(command, env=env, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"dbt command failed with exit code {exc.returncode}. "
            "Check that PostgreSQL is running and the dbt profile is correct."
        ) from exc


def main() -> None:
    dbt = _ensure_dbt_available()
    env = os.environ.copy()
    _ensure_profiles_dir(env)
    commands = [
        [dbt, "debug", "--project-dir", str(DBT_DIR)],
        [dbt, "run", "--project-dir", str(DBT_DIR)],
        [dbt, "test", "--project-dir", str(DBT_DIR)],
    ]
    for command in commands:
        _run(command, env)
    print("dbt project complete")


if __name__ == "__main__":
    main()

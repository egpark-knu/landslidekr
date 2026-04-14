"""
GEE initialization helper — reads project ID from env / config, handles auth.

Priority:
    1. GEE_PROJECT env var
    2. ~/.mas/gee.json {"project": "...", "service_account_key": "..."}
    3. ~/.config/earthengine/credentials (user OAuth)
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional


def init_ee(project: Optional[str] = None) -> dict:
    """
    Initialize Earth Engine with project ID.

    Returns:
        dict: {project, auth_mode} on success
    """
    import ee

    # Resolve project
    project = project or os.environ.get("GEE_PROJECT")
    if not project:
        cfg = Path.home() / ".mas" / "gee.json"
        if cfg.exists():
            with open(cfg) as f:
                data = json.load(f)
            project = data.get("project")

    if not project:
        raise RuntimeError(
            "GEE project not set. Configure via GEE_PROJECT env var or ~/.mas/gee.json"
        )

    # Try service-account first (if configured)
    cfg = Path.home() / ".mas" / "gee.json"
    if cfg.exists():
        with open(cfg) as f:
            data = json.load(f)
        sa_key = data.get("service_account_key")
        sa_email = data.get("service_account_email")
        if sa_key and sa_email:
            creds = ee.ServiceAccountCredentials(sa_email, sa_key)
            ee.Initialize(credentials=creds, project=project)
            return {"project": project, "auth_mode": "service_account"}

    # Fallback to user OAuth
    ee.Initialize(project=project)
    return {"project": project, "auth_mode": "user_oauth"}


if __name__ == "__main__":
    import sys
    try:
        info = init_ee()
        print(json.dumps(info, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

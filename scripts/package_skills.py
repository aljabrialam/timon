"""Package each skills/<name>/ folder as dist/<name>.zip for Qoder Cloud Agents upload.

QCA rules: one zip per skill, exactly one top-level folder matching `name` in SKILL.md,
SKILL.md with name + description frontmatter, <= 50 MB.
Usage: python scripts/package_skills.py
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS, DIST = ROOT / "skills", ROOT / "dist"
SKIP = {".DS_Store", "__pycache__", ".git"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def frontmatter(md: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", md, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def main() -> int:
    DIST.mkdir(exist_ok=True)
    ok = True
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        md = d / "SKILL.md"
        fm = frontmatter(md.read_text()) if md.exists() else {}
        name, desc = fm.get("name", ""), fm.get("description", "")
        problems = []
        if not md.exists():
            problems.append("missing SKILL.md")
        if name != d.name:
            problems.append(f"name '{name}' != folder '{d.name}'")
        if not NAME_RE.match(name or ""):
            problems.append("invalid name")
        if not desc or len(desc) > 5120:
            problems.append("description missing or > 5120 chars")
        if problems:
            ok = False
            print(f"FAIL {d.name}: {'; '.join(problems)}")
            continue
        out = DIST / f"{name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in d.rglob("*"):
                if f.is_file() and not (set(f.parts) & SKIP):
                    z.write(f, Path(name) / f.relative_to(d))
        size = out.stat().st_size
        print(f"OK   {out.relative_to(ROOT)} ({size/1024:.1f} KB) — local check only; QCA upload decides")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

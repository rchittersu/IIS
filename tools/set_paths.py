#!/usr/bin/env python3
"""Fill the {{TOKEN}} path placeholders used across the repo with local paths.

    python tools/set_paths.py                 # apply configs/paths.env
    python tools/set_paths.py --env my.env    # apply another env file
    python tools/set_paths.py --reverse       # restore the {{TOKEN}} placeholders
    python tools/set_paths.py --check         # list files that still contain placeholders

The applied mapping is stored in .paths_applied.json so --reverse can undo it.
Large data and checkpoint folders (data/, inference/runs/) are never touched.
"""
import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, ".paths_applied.json")
EXT = (".py", ".sh", ".yaml", ".yml", ".ipynb", ".md", ".txt", ".cfg")
SKIP_DIRS = {"data", "runs", ".git", "__pycache__"}
SKIP_FILES = {"set_paths.py", "paths.env", "README.md"}
TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")


def load_env(path):
    env = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = os.path.expanduser(v.strip().strip('"').strip("'")).rstrip("/")
    if not env.get("PROJECT_ROOT"):
        env["PROJECT_ROOT"] = REPO
    return env


def files():
    for dp, dn, fn in os.walk(REPO):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(EXT) and f not in SKIP_FILES:
                yield os.path.join(dp, f)


def rewrite(pairs):
    changed = 0
    for p in files():
        try:
            s = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        o = s
        for a, b in pairs:
            s = s.replace(a, b)
        if s != o:
            open(p, "w", encoding="utf-8").write(s)
            changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", default=os.path.join(REPO, "configs", "paths.env"))
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.check:
        left = {}
        for p in files():
            try:
                for t in TOKEN.findall(open(p, encoding="utf-8").read()):
                    left.setdefault(t, set()).add(os.path.relpath(p, REPO))
            except UnicodeDecodeError:
                pass
        for t, fs in sorted(left.items()):
            print(f"{{{{{t}}}}}: {len(fs)} files")
        return 0 if not left else 1

    if a.reverse:
        if not os.path.exists(STATE):
            sys.exit("nothing to reverse (.paths_applied.json not found)")
        applied = json.load(open(STATE))
        # longest value first so nested paths (e.g. PROJECT_ROOT inside another root) restore correctly
        pairs = sorted(((v, "{{%s}}" % k) for k, v in applied.items() if v), key=lambda x: -len(x[0]))
        n = rewrite(pairs)
        os.remove(STATE)
        print(f"restored placeholders in {n} files")
        return 0

    if os.path.exists(STATE):
        sys.exit("paths already applied; run --reverse first, then apply the new env")
    env = load_env(a.env)
    used = set()
    for p in files():
        try:
            used |= set(TOKEN.findall(open(p, encoding="utf-8").read()))
        except UnicodeDecodeError:
            pass
    missing = sorted(t for t in used if not env.get(t) or env[t].startswith("/path/to"))
    if missing:
        print("warning: not configured (left as placeholders):", ", ".join(missing))
    applied = {t: env[t] for t in used if t not in missing}
    n = rewrite([("{{%s}}" % k, v) for k, v in applied.items()])
    json.dump(applied, open(STATE, "w"), indent=2)
    print(f"applied {len(applied)} paths in {n} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

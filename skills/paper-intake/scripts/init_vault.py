#!/usr/bin/env python3
"""Create a new reading vault from the bundled template; never merge existing data."""
from pathlib import Path
import argparse, json, shutil, sys

def create_vault(destination):
    dest = Path(destination).expanduser().absolute()
    source = Path(__file__).resolve().parents[1] / "assets/vault-template"
    resolved = dest.resolve()
    if resolved == source or source in resolved.parents:
        raise ValueError("Destination must be outside the packaged template")
    if dest.exists() or dest.is_symlink():
        raise ValueError("Destination already exists; choose a new folder")
    if not dest.parent.is_dir():
        raise ValueError("Destination parent must already exist")
    shutil.copytree(source, dest)
    for keep in dest.rglob(".gitkeep"):
        keep.unlink()
    return {"status": "created", "vault": str(dest),
            "entry": "10 文献/文献入口.md", "default_destination_changed": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True)
    args = parser.parse_args()
    print(json.dumps(create_vault(args.vault), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

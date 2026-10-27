#!/usr/bin/env python3
"""Create a new reading vault from the bundled template; never merge existing data."""
from pathlib import Path
import argparse, json, shutil, sys

def create_vault(destination):
    dest = Path(destination).expanduser().absolute()
    assets = Path(__file__).resolve().parents[1] / "assets"
    source = assets / "vault-template"
    config = assets / "obsidian-config"
    resolved = dest.resolve()
    if resolved == assets or assets in resolved.parents:
        raise ValueError("Destination must be outside the packaged template")
    if dest.exists() or dest.is_symlink():
        raise ValueError("Destination already exists; choose a new folder")
    if not dest.parent.is_dir():
        raise ValueError("Destination parent must already exist")
    required = ['academic-workbench.json', 'app.json', 'appearance.json',
                'community-plugins.json', 'core-plugins.json', 'templates.json',
                'plugins/academic-library-helper/main.js',
                'plugins/academic-library-helper/manifest.json']
    for name in required:
        if not (config / name).is_file():
            raise ValueError('Package configuration missing: ' + name)
    shutil.copytree(source, dest)
    shutil.copytree(config, dest / '.obsidian')
    for folder in ['10 文献/PDF', '10 文献/阅读笔记',
                   '10 文献/AI辅助阅读', '10 文献/阅读工具/附件']:
        (dest / folder).mkdir(parents=True, exist_ok=True)
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

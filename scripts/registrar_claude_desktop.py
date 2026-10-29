"""Register this MCP server in Claude Desktop's claude_desktop_config.json.

Idempotent: adds or updates only mcpServers["aladin"] and keeps every other key.
Close Claude Desktop completely before running it: the app rewrites the file from
memory while open and can drop keys added from outside.

Run from the repository root:  .venv/bin/python scripts/registrar_claude_desktop.py
"""

import json
import platform
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PYTHON = REPO / ".venv" / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")


def config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if system == "Windows":
        import os
        return Path(os.environ["APPDATA"]) / "Claude/claude_desktop_config.json"
    return Path.home() / ".config/Claude/claude_desktop_config.json"


def main() -> None:
    if not PYTHON.exists():
        sys.exit(f"Virtual environment not found at {PYTHON}. Create it first (see README).")
    path = config_path()
    config = json.loads(path.read_text()) if path.exists() else {}
    entry = {"command": str(PYTHON), "args": ["-m", "aladin_mcp.server"], "cwd": str(REPO)}
    if config.get("mcpServers", {}).get("aladin") == entry:
        print(f"Already registered in {path}")
        return
    if path.exists():
        shutil.copy(path, path.with_suffix(".json.bak"))
    config.setdefault("mcpServers", {})["aladin"] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    print(f"Registered 'aladin' in {path} (backup: {path.with_suffix('.json.bak').name})")
    print("Start Claude Desktop again to load it.")


if __name__ == "__main__":
    main()

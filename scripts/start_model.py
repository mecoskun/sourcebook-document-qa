"""Run the shared CPU model service; no GPU or external inference API required."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    local = list((ROOT / ".runtime").rglob("llama-server.exe"))
    executable = str(local[0]) if local else shutil.which("llama-server")
    if not executable or not (ROOT / ".models" / "model.gguf").exists():
        raise SystemExit("Run python scripts/prepare_models.py first; on Linux install llama-server.")
    subprocess.run([executable, "-m", str(ROOT / ".models" / "model.gguf"),
                    "--host", "127.0.0.1", "--port", "8081", "--alias", "sourcebook",
                    "-c", "8192", "-t", "4", "-ngl", "0", "--parallel", "1",
                    "--jinja", "--reasoning", "off", "--reasoning-budget", "0",
                    "--chat-template-file", str(ROOT / "configs" / "qwen3-no-thinking.jinja"),
                    "--cors-origins", "http://127.0.0.1:8081"], check=True, cwd=ROOT)

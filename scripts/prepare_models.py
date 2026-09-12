"""Download public model assets and (on Windows) the official CPU runtime locally."""
import argparse
import hashlib
import json
import os
import sys
import tarfile
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from app.retrieval import DocumentIndex  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-tag", choices=["1.7b", "4b"])
    args = parser.parse_args()
    model_dir = ROOT / ".models"
    runtime_dir = ROOT / ".runtime"
    model_dir.mkdir(exist_ok=True)
    runtime_dir.mkdir(exist_ok=True)
    manifest_path = ROOT / "models.lock.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if args.model_tag and manifest.get("model", {}).get("tag") != args.model_tag:
        target = model_dir / "model.gguf"
        if target.exists():
            previous = manifest.get("model", {}).get("tag", "previous")
            target.rename(model_dir / f"model-{previous}.gguf")
        manifest.pop("model", None)
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        if "model" not in manifest:
            tag = args.model_tag or "1.7b"
            info = client.get(f"https://registry.ollama.ai/v2/library/qwen3/manifests/{tag}")
            info.raise_for_status()
            info = info.json()
            layer = next(s for s in info["layers"]
                         if s["mediaType"] == "application/vnd.ollama.image.model")
            manifest["model"] = {"registry": "https://registry.ollama.ai/v2/library/qwen3",
                                 "tag": tag, "digest": layer["digest"],
                                 "sha256": layer["digest"].split(":")[1]}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        item = manifest["model"]
        target = model_dir / "model.gguf"
        if not target.exists():
            print(f"Downloading Qwen3 {item['tag']} GGUF from Ollama's public registry...", flush=True)
            url = f"{item['registry']}/blobs/{item['digest']}"
            temp = target.with_suffix(".part")
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with temp.open("wb") as output:
                    for chunk in response.iter_bytes(1024 * 1024):
                        output.write(chunk)
            temp.replace(target)
        with target.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if item.get("sha256") and item["sha256"] != digest:
            raise RuntimeError("Model checksum mismatch")
        item["sha256"] = digest
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        if sys.platform == "win32" and not list(runtime_dir.rglob("llama-server.exe")):
            print("Downloading official llama.cpp CPU runtime...", flush=True)
            release_url = "https://api.github.com/repos/ggml-org/llama.cpp/releases/"
            release_url += "tags/" + manifest.get("runtime", {}).get("version", "b10917")
            response = client.get(release_url)
            response.raise_for_status()
            release = response.json()
            asset = next(a for a in release["assets"]
                         if a["name"].endswith("bin-win-cpu-x64.zip"))
            archive = runtime_dir / asset["name"]
            with client.stream("GET", asset["browser_download_url"]) as response:
                response.raise_for_status()
                with archive.open("wb") as output:
                    for chunk in response.iter_bytes():
                        output.write(chunk)
            with archive.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            if asset.get("digest") and asset["digest"] != "sha256:" + digest:
                raise RuntimeError("Runtime checksum mismatch")
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.infolist():
                    if not (runtime_dir / member.filename).resolve().is_relative_to(runtime_dir.resolve()):
                        raise RuntimeError("Unsafe archive path")
                bundle.extractall(runtime_dir)
            manifest["runtime"] = {"version": release["tag_name"], "asset": asset["name"],
                                   "sha256": digest}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        embedding_dir = model_dir / "embedding"
        if not (embedding_dir / "model_optimized.onnx").exists():
            print("Downloading CPU embeddings from Qdrant's published storage...", flush=True)
            url = "https://storage.googleapis.com/qdrant-fastembed/BAAI-bge-small-en.tar.gz"
            archive = model_dir / "embedding.tar.gz"
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with archive.open("wb") as output:
                    for chunk in response.iter_bytes():
                        output.write(chunk)
            with archive.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            if manifest.get("embedding", {}).get("sha256", digest) != digest:
                raise RuntimeError("Embedding archive checksum mismatch")
            with tarfile.open(archive) as bundle:
                bundle.extractall(model_dir / "embedding-extract", filter="data")
            source = next((model_dir / "embedding-extract").rglob("model_optimized.onnx")).parent
            source.rename(embedding_dir)
            manifest["embedding"] = {"name": "BAAI/bge-small-en", "url": url, "sha256": digest}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Preparing CPU embedding model...", flush=True)
    list(DocumentIndex().encoder.embed(["Model warmup"]))
    print("Models ready. No paid inference API is used.", flush=True)


if __name__ == "__main__":
    main()

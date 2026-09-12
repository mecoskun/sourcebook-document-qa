"""Short-lived parser process: bounded input, timeout in parent, Linux memory limit."""
import json
import sys

from app.config import settings
from app.extraction import extract

if __name__ == "__main__":
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
    try:
        data = sys.stdin.buffer.read(settings.max_file_bytes + 1)
        print(json.dumps({"sections": extract(data, sys.argv[1])}))
    except Exception as exc:
        message = str(exc) if isinstance(exc, ValueError) else "The document could not be parsed."
        print(json.dumps({"error": message}))

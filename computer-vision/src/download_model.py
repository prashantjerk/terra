"""Download the ~23 MB MobileNet-SSD model once; verify its contents."""
import hashlib
from pathlib import Path
from urllib.request import urlopen

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
FILES = {
    "deploy.prototxt": "2d180f723b3109e21f8287f6b3c691390d07b60eed998327cd3259ffa0e50608",
    "mobilenet_iter_73000.caffemodel": "52eed8be80522c152a17fb56740de705b79881bde1a167e0e747310523685fc7",
}
BASE = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/"


def download():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name, digest in FILES.items():
        path = MODEL_DIR / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            continue
        print(f"Downloading {name}...", flush=True)
        with urlopen(BASE + name, timeout=60) as response:
            content = response.read(30 * 1024 * 1024)
        if hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError(f"Checksum mismatch for {name}; model was not saved")
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
    print(f"Model ready in {MODEL_DIR}")


if __name__ == "__main__":
    download()

"""Provision the AutoDock Vina binary (idempotent, checksum-verified).

The pip `vina` package is deliberately NOT a dependency: it ships no Windows
wheels and its sdist build fails here. We run the official release binary as a
subprocess instead, in local dev and in Docker alike, so there is exactly one
docking code path.

Hash provenance: the v1.2.7 GitHub release publishes no `digest` field, so the
SHA-256 values below are trust-on-first-use -- computed from the downloaded
bytes and pinned here so a later swap or corruption is caught. The Windows
binary has been executed on the dev machine; the Linux binary is first executed
during the Docker build.

Run: python scripts/fetch_vina.py
"""

import hashlib
import os
import platform
import sys
import urllib.request
from pathlib import Path

VINA_VERSION = "1.2.7"
RELEASE = f"https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v{VINA_VERSION}"
BIN_DIR = Path(__file__).resolve().parent.parent / "bin"

# asset name -> sha256 (trust-on-first-use; see module docstring)
ASSETS: dict[str, str] = {
    "vina_1.2.7_win.exe":
        "e0c4b2715e0c1a74f6e92d0f3be0328ac97542eafbc111e6b1efad897a73cce5",
    "vina_1.2.7_linux_x86_64":
        "f31f774f723bba7bbe6e9d1c47577020eea9a8da16424284c043d22593570644",
    "vina_1.2.7_linux_aarch64":
        "d30c18a7d5f6f8ea9146e1cbc0aa7ade0bbb105b54ece08b4e5a7fa53edb6c62",
    "vina_1.2.7_mac_x86_64":
        "9f44ccbb163223613283a75d0be53235d9e63f4da08292cb7196144f9838b7f9",
    "vina_1.2.7_mac_aarch64":
        "823c2bbacf26d72183861322345f0a89736aca66c8e81054c66f93af5ad623f1",
}


def platform_asset() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return "vina_1.2.7_win.exe"
    if system == "Linux":
        if machine in ("x86_64", "amd64"):
            return "vina_1.2.7_linux_x86_64"
        if machine in ("aarch64", "arm64"):
            return "vina_1.2.7_linux_aarch64"
    if system == "Darwin":
        if machine in ("x86_64", "amd64"):
            return "vina_1.2.7_mac_x86_64"
        if machine in ("aarch64", "arm64"):
            return "vina_1.2.7_mac_aarch64"
    raise SystemExit(
        f"unsupported platform {system}/{platform.machine()}. "
        f"Supported: Windows, Linux x86_64/aarch64, macOS x86_64/aarch64. "
        f"Vina {VINA_VERSION} is pinned in ASSETS -- add the asset for this "
        "platform before retrying."
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    asset = platform_asset()
    expected = ASSETS[asset]
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    dest = BIN_DIR / asset

    if dest.exists() and sha256(dest) == expected:
        print(f"vina {VINA_VERSION} already present and verified: {dest}")
        return 0

    if dest.exists():
        print(f"checksum mismatch on existing {dest} -- re-downloading")
    print(f"downloading {RELEASE}/{asset}")
    tmp = dest.with_suffix(f".{os.getpid()}.tmp")
    try:
        with urllib.request.urlopen(f"{RELEASE}/{asset}", timeout=300) as resp:
            tmp.write_bytes(resp.read())
        actual = sha256(tmp)
        if actual != expected:
            tmp.unlink(missing_ok=True)
            print(
                f"CHECKSUM MISMATCH for {asset}\n  expected {expected}\n  actual   {actual}\n"
                "Refusing to install. Delete backend/bin and retry, or re-pin after "
                "verifying the upstream release.",
                file=sys.stderr,
            )
            return 1
        if platform.system() != "Windows":
            os.chmod(tmp, 0o755)
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)

    print(f"installed vina {VINA_VERSION} -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

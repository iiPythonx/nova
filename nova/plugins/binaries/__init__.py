# Copyright (c) 2025 iiPython

# Modules
import os
import tarfile
import zipfile
import platform
import subprocess
from pathlib import Path

from urllib.request import urlopen

from rich.progress import Progress

# Path initialization
NOVA_CACHE_LOCATION = Path.home() / ("AppData/Local/nova" if os.name == "nt" else ".cache/nova")

# Binary information
BINARY_URLS = {
    "swc": {
        "linux": {
            "64": "https://github.com/swc-project/swc/releases/download/v1.11.0-nightly-20250224.1/swc-linux-x64-musl",
            "A64": "https://github.com/swc-project/swc/releases/download/v1.11.0-nightly-20250224.1/swc-linux-arm64-musl"
        },
        "windows": {
            "32": "https://github.com/swc-project/swc/releases/download/v1.11.0-nightly-20250224.1/swc-win32-ia32-msvc.exe",
            "64": "https://github.com/swc-project/swc/releases/download/v1.11.0-nightly-20250224.1/swc-win32-x64-msvc.exe",
            "A64": "https://github.com/swc-project/swc/releases/download/v1.11.0-nightly-20250224.1/swc-win32-arm64-msvc.exe"
        }
    },
    "sass": {
        "linux": {
            "64": "https://github.com/sass/dart-sass/releases/download/1.85.1/dart-sass-1.85.1-linux-x64.tar.gz",
            "A64": "https://github.com/sass/dart-sass/releases/download/1.85.1/dart-sass-1.85.1-linux-arm64.tar.gz",
            "F": "dart-sass/sass"
        },
        "windows": {
            "32": "https://github.com/sass/dart-sass/releases/download/1.85.1/dart-sass-1.85.1-windows-ia32.zip",
            "64": "https://github.com/sass/dart-sass/releases/download/1.85.1/dart-sass-1.85.1-windows-x64.zip",
            "A64": "https://github.com/sass/dart-sass/releases/download/1.85.1/dart-sass-1.85.1-windows-arm64.zip",
            "F": "dart-sass/sass.bat"
        }
    },
    "minhtml": {
        "linux": {
            "64": "https://github.com/wilsonzlin/minify-html/releases/download/v0.15.0/minhtml-0.15.0-x86_64-unknown-linux-gnu",
            "A64": "https://github.com/wilsonzlin/minify-html/releases/download/v0.15.0/minhtml-0.15.0-aarch64-unknown-linux-gnu"
        },
        "windows": {
            "64": "https://github.com/wilsonzlin/minify-html/releases/download/v0.15.0/minhtml-0.15.0-x86_64-pc-windows-msvc.exe"
        }
    },
    "bun": {
        "linux": {
            "64": "https://github.com/oven-sh/bun/releases/download/bun-v1.2.3/bun-linux-x64.zip",
            "F": "bun-linux-x64/bun"
        },
        "windows": {
            "64": "https://github.com/oven-sh/bun/releases/download/bun-v1.2.3/bun-windows-x64.zip",
            "F": "bun-windows-x64/bun.exe"
        }
    },
    "uglifyjs": {
        "linux": {
            "64": "https://github.com/mishoo/UglifyJS/archive/refs/tags/v3.19.3.zip",
            "F": "UglifyJS-3.19.3/bin/uglifyjs"
        },
        "windows": {
            "64": "https://github.com/mishoo/UglifyJS/archive/refs/tags/v3.19.3.zip",
            "F": "UglifyJS-3.19.3/bin/uglifyjs"
        }
    },
    "csso": {
        "linux": {
            "64": "https://github.com/css/csso-cli/archive/refs/tags/v4.0.2.zip",
            "F": "csso-cli-4.0.2/bin/csso"
        },
        "windows": {
            "64": "https://github.com/css/csso-cli/archive/refs/tags/v4.0.2.zip",
            "F": "csso-cli-4.0.2/bin/csso"
        }
    }
}

# Handle fetching
def fetch_os() -> str:
    return {"nt": "windows", "posix": "linux"}[os.name]

def download_asset(name: str) -> None:
    if not NOVA_CACHE_LOCATION.is_dir():
        NOVA_CACHE_LOCATION.mkdir()

    system, data = fetch_os(), BINARY_URLS[name]
    bitting = {"i386": "32", "x86_64": "64", "AMD64": "64", "aarch64": "A64"}[platform.machine()]

    # Fetch the latest release
    download_url = data.get(system, {}).get(bitting)
    if download_url is None:
        print(f"No download for '{name}' was found for this '{system}-{bitting}' system!")
        return

    file = NOVA_CACHE_LOCATION / name

    # Download file
    with urlopen(download_url) as response:
        with file.open("wb") as output:
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Downloading {name}...", total = int(response.getheader("Content-Length") or 0))
                for chunk in iter(lambda: response.read(1024), b""):
                    output.write(chunk)
                    progress.update(task, advance = len(chunk))

    # Handle decompression
    if download_url.endswith(".tar.gz"):
        with tarfile.open(file, "r:gz") as tar_file:
            tar_file.extractall(NOVA_CACHE_LOCATION, filter = "fully_trusted")

        os.remove(file)

    if download_url.endswith(".zip"):
        with zipfile.ZipFile(file, "r") as zip_file:
            zip_file.extractall(NOVA_CACHE_LOCATION)

        os.remove(file)

    if system == "linux":
        subprocess.run(["chmod", "+x", NOVA_CACHE_LOCATION / str(data[system].get("F", name))])

def fetch_binary(name: str) -> Path:
    path = NOVA_CACHE_LOCATION / BINARY_URLS[name][fetch_os()].get("F", name)
    if not path.is_file():
        download_asset(name)

    return path

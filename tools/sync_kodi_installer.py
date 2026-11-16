#!/usr/bin/env python3
"""Keep a Kodi-file-manager-installable repository ZIP at the website root.

GitHub Pages does not provide automatic directory listings, so index.html
contains an ordinary static anchor to repository.nebelkind.zip. The actual
ZIP is mirrored from the verified Nebelkind Kodi repository.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://raw.githubusercontent.com/schlimmtendo/nebelkind.repo/main/"
ID = "repository.nebelkind"
VERSION_RE = re.compile(r"^[0-9][A-Za-z0-9._+-]*$")

def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Nebelkind-Kodi-Pages-Sync/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def main() -> None:
    remote = ET.fromstring(get(SOURCE + ID + "/addon.xml"))
    version = remote.get("version", "")
    if remote.get("id") != ID or not VERSION_RE.fullmatch(version):
        raise ValueError("Unexpected official Kodi repository descriptor")
    url = SOURCE + "packages/" + ID + "/" + ID + "-" + version + ".zip"
    payload = get(url)
    if not 100 < len(payload) < 5_000_000:
        raise ValueError("Unexpected Kodi repository ZIP size")
    with ZipFile(BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Damaged Kodi repository ZIP")
        inner = ET.fromstring(archive.read(ID + "/addon.xml"))
        if inner.get("id") != ID or inner.get("version") != version:
            raise ValueError("Repository ZIP is not the published requested version")
    new_name = ID + "-" + version + ".zip"
    # Stage bytes fully before replacing either downloadable ZIP.
    for filename in (new_name, ID + ".zip"):
        target = ROOT / filename
        if target.is_file() and target.read_bytes() == payload:
            continue
        with tempfile.NamedTemporaryFile(dir=ROOT, prefix="neb-repo-", suffix=".tmp", delete=False) as f:
            tmp = Path(f.name)
            f.write(payload)
        tmp.replace(target)
        print("Prepared:", filename)
    # Deletion is included with the new file in the same Git commit.
    for old in ROOT.glob(ID + "-*.zip"):
        if old.name != new_name:
            old.unlink()
            print("Retired:", old.name)
    print("Repo installer mirrored and verified:", new_name)

if __name__ == "__main__":
    main()

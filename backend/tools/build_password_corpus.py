"""Reproduce exact-match denylist digests from pinned sources; no network at login."""

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

source = Path(sys.argv[1])
target = Path(__file__).resolve().parents[1] / "src/y3management/iam/data"
manifest = json.loads((target / "source-manifest.json").read_text())
words: set[str] = set()
for item in manifest["files"]:
    raw = (source / item["file"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise SystemExit("CORPUS_SOURCE_INTEGRITY_FAILED")
    if item["file"].endswith(".txt"):
        words.update(
            unicodedata.normalize("NFC", line.removesuffix("\r"))
            for line in raw.decode("utf-8", "strict").split("\n")
        )
seeds = {"password", "administrator", "qwerty", "letmein"}
assert seeds <= words
eligible = sorted(word for word in words if 15 <= len(word) <= 128)
digests = sorted(hashlib.sha256(word.encode("utf-8")).hexdigest() for word in eligible)
assert len(set(digests)) == len(eligible)
payload = ("\n".join(digests) + "\n").encode()
seed_payload = ("\n".join(sorted(seeds)) + "\n").encode()
if "--check" in sys.argv:
    assert (target / "blocked-sha256.txt").read_bytes() == payload
    assert (target / "seeds.txt").read_bytes() == seed_payload
else:
    (target / "blocked-sha256.txt").write_bytes(payload)
    (target / "seeds.txt").write_bytes(seed_payload)
print(
    json.dumps(
        {
            "eligible": len(eligible),
            "seeds": len(seeds),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
)

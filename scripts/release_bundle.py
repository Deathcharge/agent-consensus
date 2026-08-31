"""Create or verify a bounded wheel/sdist checksum receipt using only the standard library.

This is release tooling, not part of the runtime API. Receipts are not signatures:
obtain the expected commit and manifest digest from a separately trusted CI run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

MANIFEST = "release-manifest.json"
MAX_ARTIFACT_BYTES = 100 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
_VERSION = r"[A-Za-z0-9][A-Za-z0-9.!+_]{0,127}"


class BundleError(ValueError):
    """The candidate directory or its receipt violates the bundle contract."""


def _hex(value: Any, length: int, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise BundleError(f"{label} must be {length} lowercase hexadecimal characters")
    return value


def _names(version: Any) -> tuple[str, str]:
    if not isinstance(version, str) or not re.fullmatch(_VERSION, version):
        raise BundleError("unsupported artifact version spelling")
    return (
        f"agent_consensus-{version}-py3-none-any.whl",
        f"agent_consensus-{version}.tar.gz",
    )


def _inventory(directory: Path, expected: set[str]) -> None:
    entries = list(directory.iterdir())
    if {entry.name for entry in entries} != expected:
        raise BundleError("candidate directory must contain exactly the expected bundle files")
    if any(entry.is_symlink() or not entry.is_file() for entry in entries):
        raise BundleError("bundle entries must be regular files, not links or directories")


def _fingerprint(path: Path, limit: int) -> tuple[int, str]:
    if path.is_symlink() or not path.is_file():
        raise BundleError("bundle entries must be regular files")
    if not 0 < path.stat().st_size <= limit:
        raise BundleError("bundle file is empty or exceeds its size limit")
    size = 0
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise BundleError("bundle file exceeds its size limit")
            digest.update(chunk)
    if size == 0:
        raise BundleError("bundle file is empty")
    return size, digest.hexdigest()


def create_bundle(directory: Path, source_commit: str) -> str:
    """Write one exclusive receipt after the caller has tested the two artifacts."""
    _hex(source_commit, 40, "source commit")
    wheels = list(directory.glob("*.whl"))
    if len(wheels) != 1:
        raise BundleError("expected one core wheel")
    match = re.fullmatch(rf"agent_consensus-({_VERSION})-py3-none-any\.whl", wheels[0].name)
    if match is None:
        raise BundleError("expected an agent-consensus pure-Python wheel")
    version = match.group(1)
    names = _names(version)
    _inventory(directory, set(names))
    artifacts = []
    for name in names:
        size, digest = _fingerprint(directory / name, MAX_ARTIFACT_BYTES)
        artifacts.append({"filename": name, "size_bytes": size, "sha256": digest})
    receipt = {
        "schema_version": 1,
        "package": "agent-consensus",
        "version": version,
        "source_commit": source_commit,
        "artifacts": artifacts,
    }
    payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    # Never overwrite an earlier receipt or silently bless a modified bundle.
    with (directory / MANIFEST).open("xb") as stream:
        stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BundleError("duplicate receipt key")
        result[key] = value
    return result


def verify_bundle(directory: Path, source_commit: str, manifest_sha256: str) -> dict[str, Any]:
    """Verify identity, inventory, sizes and hashes without extracting or executing files."""
    _hex(source_commit, 40, "source commit")
    _hex(manifest_sha256, 64, "manifest SHA-256")
    manifest_path = directory / MANIFEST
    _fingerprint(manifest_path, MAX_MANIFEST_BYTES)
    with manifest_path.open("rb") as stream:
        payload = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(payload) > MAX_MANIFEST_BYTES:
        raise BundleError("receipt exceeds its size limit")
    if hashlib.sha256(payload).hexdigest() != manifest_sha256:
        raise BundleError("receipt does not match the trusted manifest SHA-256")
    try:
        receipt = json.loads(payload, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise BundleError("invalid JSON receipt") from error
    if not isinstance(receipt, dict) or set(receipt) != {
        "schema_version",
        "package",
        "version",
        "source_commit",
        "artifacts",
    }:
        raise BundleError("unexpected receipt fields")
    if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1:
        raise BundleError("unsupported receipt schema")
    if receipt["package"] != "agent-consensus" or receipt["source_commit"] != source_commit:
        raise BundleError("receipt package or source commit does not match")
    names = _names(receipt["version"])
    _inventory(directory, {*names, MANIFEST})
    artifacts = receipt["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        raise BundleError("receipt must describe exactly two artifacts")
    seen: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"filename", "size_bytes", "sha256"}:
            raise BundleError("unexpected artifact fields")
        name = artifact["filename"]
        if not isinstance(name, str) or name not in names or name in seen:
            raise BundleError("unexpected or duplicate artifact filename")
        seen.add(name)
        if (
            type(artifact["size_bytes"]) is not int
            or not 0 < artifact["size_bytes"] <= MAX_ARTIFACT_BYTES
        ):
            raise BundleError("invalid artifact size")
        _hex(artifact["sha256"], 64, "artifact SHA-256")
        actual = _fingerprint(directory / name, MAX_ARTIFACT_BYTES)
        if actual != (artifact["size_bytes"], artifact["sha256"]):
            raise BundleError(f"artifact checksum or size mismatch: {name}")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("create", "verify"):
        subparser = commands.add_parser(command)
        subparser.add_argument("--dist", type=Path, required=True)
        subparser.add_argument("--source-commit", required=True)
        if command == "verify":
            subparser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            digest = create_bundle(args.dist, args.source_commit)
            print(f"Manifest SHA-256: {digest}")
        else:
            receipt = verify_bundle(args.dist, args.source_commit, args.manifest_sha256)
            print(f"Verified {receipt['package']} {receipt['version']} at {args.source_commit}")
    except (BundleError, OSError) as error:
        print(f"Bundle verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

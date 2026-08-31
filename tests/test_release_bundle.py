"""Release receipts bind exact bytes to independently supplied expectations, not signatures."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import release_bundle as bundle

COMMIT = "a" * 40
WHEEL, SDIST = bundle._names("0.2.0")


@pytest.fixture
def candidate(tmp_path):
    # Synthetic bytes deliberately show that this verifier does not certify package contents.
    (tmp_path / WHEEL).write_bytes(b"wheel bytes")
    (tmp_path / SDIST).write_bytes(b"sdist bytes")
    return tmp_path


def rewrite_receipt(directory, change):
    path = directory / bundle.MANIFEST
    receipt = json.loads(path.read_bytes())
    change(receipt)
    payload = json.dumps(receipt).encode()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def test_round_trip_is_deterministic_and_read_only(candidate, tmp_path_factory):
    digest = bundle.create_bundle(candidate, COMMIT)
    receipt = bundle.verify_bundle(candidate, COMMIT, digest)
    assert receipt["version"] == "0.2.0"
    assert {item["filename"] for item in receipt["artifacts"]} == {WHEEL, SDIST}
    assert str(candidate) not in (candidate / bundle.MANIFEST).read_text()
    other = tmp_path_factory.mktemp("other")
    for name in (WHEEL, SDIST):
        (other / name).write_bytes((candidate / name).read_bytes())
    assert bundle.create_bundle(other, COMMIT) == digest
    assert bundle.verify_bundle(candidate, COMMIT, digest) == receipt


def test_existing_receipt_is_never_overwritten(candidate):
    bundle.create_bundle(candidate, COMMIT)
    original = (candidate / bundle.MANIFEST).read_bytes()
    with pytest.raises(bundle.BundleError):
        bundle.create_bundle(candidate, COMMIT)
    assert (candidate / bundle.MANIFEST).read_bytes() == original


@pytest.mark.parametrize("name", [WHEEL, SDIST])
def test_changed_artifact_fails(candidate, name):
    digest = bundle.create_bundle(candidate, COMMIT)
    (candidate / name).write_bytes(b"changed")
    with pytest.raises(bundle.BundleError, match="checksum or size"):
        bundle.verify_bundle(candidate, COMMIT, digest)


def test_expected_commit_and_manifest_digest_are_independent(candidate):
    digest = bundle.create_bundle(candidate, COMMIT)
    with pytest.raises(bundle.BundleError, match="source commit"):
        bundle.verify_bundle(candidate, "b" * 40, digest)
    with pytest.raises(bundle.BundleError, match="trusted manifest"):
        bundle.verify_bundle(candidate, COMMIT, "0" * 64)
    (candidate / bundle.MANIFEST).write_bytes(b"{}")
    with pytest.raises(bundle.BundleError, match="trusted manifest"):
        bundle.verify_bundle(candidate, COMMIT, digest)


@pytest.mark.parametrize("extra", ["extra.whl", ".hidden", "unexpected-directory"])
def test_extra_inventory_fails(candidate, extra):
    digest = bundle.create_bundle(candidate, COMMIT)
    if extra == "unexpected-directory":
        (candidate / extra).mkdir()
    else:
        (candidate / extra).write_bytes(b"extra")
    with pytest.raises(bundle.BundleError, match="exactly"):
        bundle.verify_bundle(candidate, COMMIT, digest)


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value.update(schema_version=True),
        lambda value: value.update(schema_version=2),
        lambda value: value.update(package="another-package"),
        lambda value: value.update(version="../../escape"),
        lambda value: value.update(unexpected="field"),
        lambda value: value.update(artifacts=[]),
        lambda value: value["artifacts"][0].update(filename="../outside.whl"),
        lambda value: value["artifacts"][0].update(filename="C:\\outside.whl"),
        lambda value: value["artifacts"][0].update(size_bytes=True),
        lambda value: value["artifacts"][0].update(size_bytes=-1),
        lambda value: value["artifacts"][0].update(sha256="not-a-digest"),
        lambda value: value["artifacts"].__setitem__(1, value["artifacts"][0]),
    ],
)
def test_receipt_schema_is_validated_even_with_matching_digest(candidate, change):
    bundle.create_bundle(candidate, COMMIT)
    digest = rewrite_receipt(candidate, change)
    with pytest.raises(bundle.BundleError):
        bundle.verify_bundle(candidate, COMMIT, digest)


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b"[]", b"invalid JSON", b"\xff"])
def test_invalid_json_receipts_fail(candidate, payload):
    (candidate / bundle.MANIFEST).write_bytes(payload)
    with pytest.raises(bundle.BundleError):
        bundle.verify_bundle(candidate, COMMIT, hashlib.sha256(payload).hexdigest())


def test_size_limits_and_missing_artifacts_fail(candidate, monkeypatch):
    monkeypatch.setattr(bundle, "MAX_ARTIFACT_BYTES", 3)
    with pytest.raises(bundle.BundleError, match="size limit"):
        bundle.create_bundle(candidate, COMMIT)
    (candidate / WHEEL).unlink()
    with pytest.raises(bundle.BundleError, match="one core wheel"):
        bundle.create_bundle(candidate, COMMIT)


def test_symlink_is_rejected(candidate, monkeypatch):
    # Works on Windows without requiring symlink creation privileges.
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path.name == WHEEL or original(path))
    with pytest.raises(bundle.BundleError, match="links"):
        bundle.create_bundle(candidate, COMMIT)


@pytest.mark.parametrize("commit", ["main", "A" * 40, "a" * 39, "a" * 41, True])
def test_invalid_commit_is_rejected(candidate, commit):
    with pytest.raises(bundle.BundleError, match="source commit"):
        bundle.create_bundle(candidate, commit)


def test_wrong_wheel_and_missing_archive_are_rejected(candidate):
    (candidate / WHEEL).rename(candidate / "another_package-0.2.0-py3-none-any.whl")
    with pytest.raises(bundle.BundleError, match="pure-Python wheel"):
        bundle.create_bundle(candidate, COMMIT)
    (candidate / "another_package-0.2.0-py3-none-any.whl").rename(candidate / WHEEL)
    (candidate / SDIST).unlink()
    with pytest.raises(bundle.BundleError, match="exactly"):
        bundle.create_bundle(candidate, COMMIT)


def test_missing_or_oversized_receipt_is_rejected(candidate, monkeypatch):
    with pytest.raises(bundle.BundleError, match="regular files"):
        bundle.verify_bundle(candidate, COMMIT, "0" * 64)
    digest = bundle.create_bundle(candidate, COMMIT)
    monkeypatch.setattr(bundle, "MAX_MANIFEST_BYTES", 1)
    with pytest.raises(bundle.BundleError, match="size limit"):
        bundle.verify_bundle(candidate, COMMIT, digest)


def test_artifact_record_must_be_an_exact_mapping(candidate):
    bundle.create_bundle(candidate, COMMIT)
    digest = rewrite_receipt(candidate, lambda value: value["artifacts"].__setitem__(0, {}))
    with pytest.raises(bundle.BundleError, match="artifact fields"):
        bundle.verify_bundle(candidate, COMMIT, digest)


def test_command_entrypoint_success_error_and_argument_contract(candidate, capsys):
    base = ["--dist", str(candidate), "--source-commit", COMMIT]
    assert bundle.main(["create", *base]) == 0
    digest = capsys.readouterr().out.strip().removeprefix("Manifest SHA-256: ")
    assert bundle.main(["verify", *base, "--manifest-sha256", digest]) == 0
    assert "Verified agent-consensus" in capsys.readouterr().out
    assert bundle.main(["create", *base]) == 1
    assert "Bundle verification failed" in capsys.readouterr().err
    with pytest.raises(SystemExit) as missing_digest:
        bundle.main(["verify", *base])
    assert missing_digest.value.code == 2


def test_cli_verifies_in_isolated_mode_and_returns_failure(candidate):
    script = Path(bundle.__file__).resolve()
    arguments = [sys.executable, "-I", str(script), "--help"]
    assert subprocess.run(arguments, capture_output=True, timeout=20).returncode == 0
    digest = bundle.create_bundle(candidate, COMMIT)
    arguments = [
        sys.executable,
        "-I",
        str(script),
        "verify",
        "--dist",
        str(candidate),
        "--source-commit",
        COMMIT,
        "--manifest-sha256",
        digest,
    ]
    passed = subprocess.run(arguments, capture_output=True, text=True, timeout=20)
    assert passed.returncode == 0, passed.stderr
    (candidate / WHEEL).write_bytes(b"changed")
    failed = subprocess.run(arguments, capture_output=True, text=True, timeout=20)
    assert failed.returncode == 1
    assert "checksum or size mismatch" in failed.stderr

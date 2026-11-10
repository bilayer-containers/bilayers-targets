"""Unit tests for the hail_batch target.

The generated run_batch.py is exercised without Hail installed: --help and
--dry-run stop before `hailtop` is imported, so these tests need only the
standard library. Running real batches (LocalBackend + Docker, or the Service)
is an integration concern, not covered here.
"""

import py_compile
import subprocess
import sys

import pytest

from bilayers_targets import available_ifaces


@pytest.fixture
def runner(interface_input: dict):
    available_ifaces["hail_batch"].generate(interface_input)
    path = interface_input["output_dir"] / "run_batch.py"
    assert path.is_file()
    return path


def run(path, *args):
    return subprocess.run([sys.executable, str(path), *args], capture_output=True, text=True)


def test_runner_compiles(runner) -> None:
    py_compile.compile(str(runner), doraise=True)


def test_help_lists_config_inputs_and_parameters(runner) -> None:
    result = run(runner, "--help")
    assert result.returncode == 0, result.stderr
    assert "--input_images" in result.stdout
    assert "--threshold" in result.stdout
    assert "--backend {local,service}" in result.stdout


def test_dry_run_chunks_files_and_builds_command(runner, tmp_path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    for i in range(5):
        (images / f"img_{i}.tiff").write_bytes(b"x")
    (images / "notes.txt").write_text("ignored: not a declared format")

    result = run(runner, "--input_images", str(images), "--dst", str(tmp_path / "out"), "--chunk-size", "2", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "5 files in 3 job(s)" in result.stdout
    assert "command: python -m example --input /bilayers/input_images --threshold 1.0" in result.stdout


def test_parameter_override_reaches_command(runner, tmp_path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "a.tiff").write_bytes(b"x")
    result = run(runner, "--input_images", str(images), "--dst", str(tmp_path / "out"), "--threshold", "2.5", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "--threshold 2.5" in result.stdout


def test_missing_required_input_is_an_error(runner, tmp_path) -> None:
    result = run(runner, "--dst", str(tmp_path / "out"), "--dry-run")
    assert result.returncode != 0
    assert "--input_images" in result.stderr


def test_local_backend_rejects_cloud_destination(runner, tmp_path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "a.tiff").write_bytes(b"x")
    result = run(runner, "--input_images", str(images), "--dst", "gs://bucket/out", "--dry-run")
    assert result.returncode != 0
    assert "local backend" in result.stderr


def test_generation_fails_without_a_file_input(interface_input: dict) -> None:
    interface_input = dict(interface_input, inputs={})
    with pytest.raises(RuntimeError, match="file-type input"):
        available_ifaces["hail_batch"].generate(interface_input)

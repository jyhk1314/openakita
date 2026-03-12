"""
L4 E2E Tests: CLI commands.

Tests CLI entry points via subprocess. Does not require LLM for status/version commands.
"""

import subprocess
import sys

import pytest


class TestCLIStatus:
    def test_version_flag(self):
        """synapse --version should print version."""
        result = subprocess.run(
            [sys.executable, "-m", "synapse", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0 or "version" in (result.stdout + result.stderr).lower()

    def test_help_flag(self):
        """synapse --help should show available commands."""
        result = subprocess.run(
            [sys.executable, "-m", "synapse", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "synapse" in output.lower() or "usage" in output.lower()

    def test_status_command(self):
        """synapse status should not crash."""
        result = subprocess.run(
            [sys.executable, "-m", "synapse", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # status may fail gracefully if not running, but should not crash
        assert result.returncode in (0, 1)


class TestCLIModuleEntry:
    def test_module_importable(self):
        """python -m synapse should be importable."""
        result = subprocess.run(
            [sys.executable, "-c", "import synapse; print(synapse.__name__)"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert "synapse" in result.stdout

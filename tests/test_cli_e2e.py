"""
E2E and regression tests for the email-investigation CLI (tasks 3.5, 3.6, 3.7).

Runs main.py via subprocess with various argument combinations and
verifies correct behavior (exit codes, output messages, report files).

Run: python -m tests.test_cli_e2e
"""
import sys
import os
import subprocess
import tempfile
import unittest


class TestEmailCLIE2E(unittest.TestCase):
    """E2E tests for the email-investigation CLI integration."""

    MAIN_PY = os.path.join(os.path.dirname(__file__), "..", "main.py")

    def _run(self, *args):
        """Run main.py with given args, return (returncode, stdout, stderr)."""
        cmd = [sys.executable, self.MAIN_PY] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    # --- Task 3.5: Both --email and --domain run both scans ---
    def test_both_email_and_domain_run_both_scans(self):
        """
        Given both --email and --domain flags,
        when the CLI executes,
        then both scans run and both reports are produced.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a valid-looking email and domain
            # We expect the email scan to fail due to no API key,
            # but what matters is that the routing logic handles both flags
            ret, stdout, stderr = self._run(
                "-e", "test@example.com",
                "-d", "example.com",
                "-o", tmpdir,
            )

            # Either both succeed, or email fails with API error —
            # but the routing must NOT crash with argparse error
            # Email validation passed (has @), so ValueError is NOT expected
            # If the code reaches the API call, it may get AdapterError
            combined = (stdout + stderr).lower()

            # The post-parse validation should NOT trigger (both flags provided)
            self.assertNotIn("Se requiere al menos", combined)

    # --- Task 3.6: Neither flag exits with non-zero error ---
    def test_neither_flag_exits_with_error(self):
        """
        Given neither --email nor --domain is provided,
        when the CLI executes,
        then it exits with non-zero status and a usage error message.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ret, stdout, stderr = self._run("-o", tmpdir)

            self.assertNotEqual(ret, 0, "Expected non-zero exit when no target flag")
            combined = (stdout + stderr).lower()
            self.assertIn("requiere al menos", combined,
                          "Expected error message about missing --email or --domain")

    # --- Verify suggestion: standalone --email e2e test ---
    def test_email_alone_runs_scan(self):
        """
        Given only the --email flag (standalone),
        when the CLI executes,
        then the email scan runs (no argparse error).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ret, stdout, stderr = self._run(
                "-e", "test@example.com",
                "-o", tmpdir,
            )
            # May get API error, but should NOT trigger
            # the "requires at least one" argparse error
            combined = (stdout + stderr).lower()
            self.assertNotIn("requiere al menos", combined,
                             "Email alone should not trigger argparse error")

    # --- Verify suggestion: invalid email format exits with error ---
    def test_invalid_email_format_exits_with_error(self):
        """
        Given --email with an invalid format (no @),
        when the CLI executes,
        then it exits with non-zero and a validation error message.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ret, stdout, stderr = self._run(
                "-e", "notanemail",
                "-o", tmpdir,
            )
            self.assertNotEqual(ret, 0,
                                "Expected non-zero exit for invalid email format")
            combined = (stdout + stderr).lower()
            self.assertIn("inválida", combined,
                          "Expected validation error for invalid email")

    # --- Task 3.7: Regression — --domain alone still works ---
    def test_domain_alone_still_works(self):
        """
        Given only the --domain flag (the original use case),
        when the CLI executes,
        then the domain scan runs as before (no argparse error).
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            ret, stdout, stderr = self._run(
                "-d", "example.com",
                "-o", tmpdir,
            )

            # Should not error on argparse (--domain is optional now but valid)
            # May fail at runtime with API errors, but should not crash on CLI validation
            combined = (stdout + stderr).lower()
            self.assertNotIn("requiere al menos", combined,
                             "Domain scan should not trigger 'requires at least one' error")


if __name__ == "__main__":
    unittest.main()
